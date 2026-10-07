"""Development-only checks; optional isolated PostgreSQL schema, never shared test project."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.models.user import User
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.chat_conversation import ChatConversation
from app.services import booking_chat as chat
from app.services.customer_chat import ModelUnavailable


@pytest.fixture()
def setup(monkeypatch):
    monkeypatch.setattr(settings,'salon_timezone','America/New_York')
    postgres = os.getenv('CHAT_TEST_POSTGRES') == '1'
    schema = 'chat_checks_'+uuid4().hex
    admin = None
    if postgres:
        admin = create_engine(settings.database_url)
        with admin.begin() as connection: connection.execute(text(f'CREATE SCHEMA {schema}'))
        engine = create_engine(settings.database_url, connect_args={'options':f'-csearch_path={schema}'})
    else:
        engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory=sessionmaker(bind=engine)
    db=factory()
    user=User(id=1,full_name='Private Customer',email='private@example.com',username='test',hashed_password='hash',role='customer',is_active=True)
    db.add(user)
    db.add(Service(id=1,name='Classic Haircut',price_cents=3500,duration_minutes=30))
    db.commit()
    user_data={field:getattr(user,field) for field in ['id','full_name','email','username','hashed_password','role','is_active']}
    db.close()
    def session():
        session=factory()
        if not postgres:
            original=session.execute
            def execute(statement,*args,**kwargs):
                if 'pg_advisory_xact_lock' in str(statement): return None
                return original(statement,*args,**kwargs)
            session.execute=execute
        return session
    def dependency():
        session_db=session()
        try: yield session_db
        finally: session_db.close()
    app.dependency_overrides[get_db]=dependency
    app.dependency_overrides[get_current_user]=lambda: User(**user_data)
    rate_limiter._events.clear()
    extracted=Mock(return_value=chat.Extracted(intent='booking',service_id=1,booking_date='2099-01-01',booking_time='11:00'))
    monkeypatch.setattr(chat,'extract_details',extracted)
    yield TestClient(app),session,extracted,user_data
    app.dependency_overrides.clear()
    engine.dispose()
    if admin:
        with admin.begin() as connection: connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        admin.dispose()


def send(client, **kwargs):
    return client.post('/api/chat',json={'request_id':str(uuid4()),'message':'Book a haircut tomorrow at 11 AM',**kwargs})


def offer(client):
    response=send(client)
    assert response.status_code == 200,response.text
    return response.json()


def confirm_payload(reply):
    return {'request_id':str(uuid4()),'conversation_id':reply['conversation_id'],'confirmation_id':reply['confirmation']['id'],'action':'confirm'}


def test_booking_confirmation_identity_and_utc_storage(setup):
    api,sessions,_,_=setup
    reply=offer(api)
    assert '$35.00' in reply['answer'] and '2099' in reply['answer']
    assert reply['confirmation']['timezone']=='America/New_York'
    with sessions() as db: assert db.query(Appointment).count()==0
    result=api.post('/api/chat',json=confirm_payload(reply))
    assert result.status_code==200,result.text
    assert result.json()['appointment_id']
    assert '#my-appointments' in result.json()['booking_path']
    with sessions() as db:
        appointment=db.query(Appointment).one()
        assert appointment.user_id==1 and appointment.customer_email=='private@example.com'
        assert appointment.start_time==datetime(2099,1,1,16)


def test_followup_time_keeps_current_booking(setup):
    api,_,model,_=setup
    model.return_value=chat.Extracted(intent='booking',service_id=1,booking_date='2099-01-01')
    first=send(api).json()
    assert 'AM or PM' in first['answer'] and first['confirmation'] is None
    model.return_value=chat.Extracted(intent='booking',booking_time='11:00')
    reply=send(api,message='11 AM',conversation_id=first['conversation_id']).json()
    assert reply['confirmation']['service_id']==1
    assert model.call_args.args[1]['booking_date']=='2099-01-01'


@pytest.mark.parametrize('details,expected',[(chat.Extracted(intent='booking'),'Which salon service'),(chat.Extracted(intent='booking',service_id=1),'What date'),(chat.Extracted(intent='booking',service_id=1,booking_date='2099-01-01'),'What time'),(chat.Extracted(intent='booking',ambiguous=True),'Please clarify')])
def test_missing_and_ambiguous_details(setup,details,expected):
    api,_,model,_=setup
    model.return_value=details
    reply=send(api).json()
    assert expected in reply['answer'] and reply['confirmation'] is None


def test_unavailable_slot_offers_database_alternatives(setup):
    api,sessions,_,_=setup
    with sessions() as db:
        db.add(Appointment(user_id=1,service_id=1,customer_name='Private',customer_email='private@example.com',start_time=datetime(2099,1,1,16),end_time=datetime(2099,1,1,16,30),status='pending'))
        db.commit()
    reply=offer(api)
    assert reply['confirmation'] is None
    assert 'Available alternatives' in reply['answer'] and '08:00 AM' in reply['answer']
    assert 'private@example.com' not in reply['answer']


def test_changed_details_invalidate_confirmation(setup):
    api,_,model,_=setup
    first=offer(api)
    model.return_value=chat.Extracted(intent='booking',booking_time='12:00')
    changed=send(api,message='Actually noon',conversation_id=first['conversation_id']).json()
    assert changed['confirmation']['id']!=first['confirmation']['id']
    assert api.post('/api/chat',json=confirm_payload(first)).status_code==409


def test_duplicate_confirmation_and_retry_create_once(setup):
    api,sessions,_,_=setup
    payload=confirm_payload(offer(api))
    first=api.post('/api/chat',json=payload).json()
    assert api.post('/api/chat',json=payload).json()['appointment_id']==first['appointment_id']
    payload['request_id']=str(uuid4())
    assert api.post('/api/chat',json=payload).json()['appointment_id']==first['appointment_id']
    with sessions() as db: assert db.query(Appointment).count()==1


def test_final_recheck_catches_booking_after_offer(setup):
    api,sessions,_,_=setup
    first=offer(api)
    with sessions() as db:
        db.add(Appointment(user_id=1,service_id=1,customer_name='Other',customer_email='other@example.com',start_time=datetime(2099,1,1,16),end_time=datetime(2099,1,1,16,30),status='pending'))
        db.commit()
    response=api.post('/api/chat',json=confirm_payload(first))
    assert response.status_code==200,response.text
    assert response.json()['appointment_id'] is None and response.json()['confirmation'] is None
    with sessions() as db: assert db.query(Appointment).count()==1


def test_price_change_requires_new_confirmation(setup):
    api,sessions,_,_=setup
    first=offer(api)
    with sessions() as db:
        db.get(Service,1).price_cents=4000
        db.commit()
    reply=api.post('/api/chat',json=confirm_payload(first)).json()
    assert reply['appointment_id'] is None and reply['confirmation']['price_cents']==4000
    assert reply['confirmation']['id']!=first['confirmation']['id']


def test_cancel_and_expired_conversation(setup):
    api,sessions,_,_=setup
    first=offer(api)
    cancelled=send(api,conversation_id=first['conversation_id'],action='cancel').json()
    assert cancelled['confirmation'] is None
    assert api.post('/api/chat',json=confirm_payload(first)).status_code==409
    with sessions() as db:
        db.get(ChatConversation,first['conversation_id']).expires_at=datetime(2000,1,1)
        db.commit()
    assert send(api,conversation_id=first['conversation_id']).status_code==410


def test_access_rules_and_conversation_ownership(setup):
    api,_,model,user=setup
    first=offer(api)
    user['id']=2
    assert send(api,conversation_id=first['conversation_id']).status_code==404
    user['role']='owner'
    assert send(api).status_code==403
    del app.dependency_overrides[get_current_user]
    assert send(api).status_code==401


def test_model_failure_preserves_draft_and_no_booking(setup):
    api,sessions,model,_=setup
    first=offer(api)
    model.side_effect=ModelUnavailable('AccessDeniedException')
    assert send(api,message='Change to noon',conversation_id=first['conversation_id']).status_code==503
    with sessions() as db:
        assert db.get(ChatConversation,first['conversation_id']).draft['confirmation']['id']==first['confirmation']['id']
        assert db.query(Appointment).count()==0


def test_unconfirmed_yes_cannot_create_appointment(setup):
    api,sessions,_,_=setup
    first=offer(api)
    reply=send(api,message='yes',conversation_id=first['conversation_id']).json()
    assert 'use Confirm booking' in reply['answer']
    with sessions() as db: assert db.query(Appointment).count()==0


@pytest.mark.parametrize('day,clock',[('2099-03-08','02:30'),('2099-11-01','01:30')])
def test_dst_time_requires_unambiguous_instant(day,clock):
    from zoneinfo import ZoneInfo
    # Use known 2026 US transitions rather than infer future DST law.
    day='2026-03-08' if clock=='02:30' else '2026-11-01'
    with pytest.raises(Exception) as error:
        chat.local_start({'booking_date':day,'booking_time':clock},ZoneInfo('America/New_York'))
    assert error.value.status_code==400


def test_metadata_logs_omit_customer_text(setup,caplog):
    api,_,_,_=setup
    with caplog.at_level('INFO'): offer(api)
    assert 'latency_ms=' in caplog.text and 'request_id=' in caplog.text
    assert 'private@example.com' not in caplog.text and 'Book a haircut' not in caplog.text


@pytest.mark.skipif(os.getenv('CHAT_TEST_POSTGRES')!='1',reason='PostgreSQL-only concurrency check')
def test_parallel_confirmations_are_idempotent(setup):
    api,sessions,_,_=setup
    payload=confirm_payload(offer(api))
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _: api.post('/api/chat',json=dict(payload,request_id=str(uuid4()))),range(2)))
    assert all(r.status_code==200 for r in responses),[r.text for r in responses]
    assert responses[0].json()['appointment_id']==responses[1].json()['appointment_id']
    with sessions() as db: assert db.query(Appointment).count()==1


@pytest.mark.skipif(os.getenv('CHAT_TEST_POSTGRES')!='1',reason='PostgreSQL-only overlap-race check')
def test_parallel_overlapping_different_start_times_cannot_both_book(setup):
    from app.api.appointment_routes import create_customer_appointment
    from app.schemas.appointment import AppointmentCreateAuthenticated
    from fastapi import HTTPException
    _, sessions, _, user = setup
    def book(minute):
        with sessions() as db:
            try:
                appt=create_customer_appointment(AppointmentCreateAuthenticated(service_id=1,start_time=datetime(2099,1,1,16,minute,tzinfo=timezone.utc)),User(**user),db)
                return appt.id
            except HTTPException as error:
                db.rollback()
                assert error.status_code==409
                return None
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(book,[0,15]))
    assert sum(result is not None for result in results)==1
    with sessions() as db: assert db.query(Appointment).count()==1


def test_model_output_is_strictly_validated_and_fences_supported(monkeypatch):
    from zoneinfo import ZoneInfo
    monkeypatch.setattr(settings,'bedrock_model_id','test-model')
    monkeypatch.setattr(settings,'aws_region','us-east-1')
    runtime=Mock()
    factory=Mock(return_value=runtime)
    monkeypatch.setattr(chat.boto3,'client',factory)
    runtime.converse.return_value={'output':{'message':{'content':[{'text':'```json\n{"intent":"booking","booking_time":"11:00"}\n```'}]}}}
    assert chat.extract_details('11 AM',{},[],ZoneInfo('America/New_York')).booking_time=='11:00'
    assert 'aws_access_key_id' not in factory.call_args.kwargs
    runtime.converse.return_value={'output':{'message':{'content':[{'text':'{"intent":"booking","sql":"DROP TABLE users"}'}]}}}
    with pytest.raises(ModelUnavailable): chat.extract_details('book',{},[],ZoneInfo('America/New_York'))


def test_natural_cancellation_before_confirmation_clears_pending_without_booking(setup):
    api,sessions,model,_=setup
    first=offer(api)
    model.reset_mock()
    cancelled=send(api,message='can you cancel my previous request?',conversation_id=first['conversation_id']).json()
    assert cancelled['confirmation'] is None
    assert 'No appointment was created' in cancelled['answer']
    model.assert_not_called()
    with sessions() as db:
        assert db.query(Appointment).count()==0
        assert db.get(ChatConversation,first['conversation_id']).draft=={}
    assert api.post('/api/chat',json=confirm_payload(first)).status_code==409


def test_cancellation_after_booking_identifies_committed_appointment_without_cancelling(setup):
    api,sessions,model,_=setup
    first=offer(api)
    booked=api.post('/api/chat',json=confirm_payload(first)).json()
    identifier=booked['appointment_id']
    model.reset_mock()
    response=send(api,message='can you cancel my previous request?',conversation_id=first['conversation_id']).json()
    assert f'#{identifier}' in response['answer']
    assert 'cancellation is currently unsupported' in response['answer'] and 'My Appointments' in response['answer']
    assert response['appointment_id'] is None
    model.assert_not_called()
    with sessions() as db:
        assert db.query(Appointment).count()==1
        assert db.get(Appointment,identifier).status=='pending'
        assert 'confirmation:None' not in db.get(ChatConversation,first['conversation_id']).receipts


def test_cancellation_with_pending_and_booked_requests_asks_then_clears_only_pending(setup):
    api,sessions,model,_=setup
    first=offer(api)
    booked=api.post('/api/chat',json=confirm_payload(first)).json()
    model.return_value=chat.Extracted(intent='booking',service_id=1,booking_date='2099-01-02',booking_time='11:00')
    pending=send(api,message='Book another haircut next day',conversation_id=first['conversation_id']).json()
    ambiguous=send(api,message='cancel my request',conversation_id=first['conversation_id']).json()
    assert 'Do you mean' in ambiguous['answer']
    assert ambiguous['confirmation']['id']==pending['confirmation']['id']
    model.return_value=chat.Extracted(intent='cancel',cancellation_target='pending')
    clarified=send(api,message='the pending request',conversation_id=first['conversation_id']).json()
    assert clarified['confirmation'] is None
    assert f"#{booked['appointment_id']}" in clarified['answer']
    with sessions() as db:
        assert db.query(Appointment).count()==1
        assert db.get(Appointment,booked['appointment_id']).status=='pending'


def test_explicit_existing_appointment_cancellation_preserves_pending_request(setup):
    api,sessions,_,_=setup
    first=offer(api)
    response=send(api,message='cancel my appointment',conversation_id=first['conversation_id']).json()
    assert 'cannot identify' in response['answer']
    assert response['confirmation']['id']==first['confirmation']['id']
    with sessions() as db: assert db.query(Appointment).count()==0


def test_negated_cancellation_requires_clarification_without_clearing(setup):
    api,_,_,_=setup
    first=offer(api)
    response=send(api,message="do not cancel my request",conversation_id=first['conversation_id']).json()
    assert 'Do you mean' in response['answer']
    assert response['confirmation']['id']==first['confirmation']['id']


def test_pending_appointment_cancellation_does_not_clear_new_chat_draft(setup):
    api,sessions,model,_=setup
    first=offer(api)
    booked=api.post('/api/chat',json=confirm_payload(first)).json()
    model.return_value=chat.Extracted(intent='booking',service_id=1,booking_date='2099-01-02',booking_time='11:00')
    pending=send(api,message='Book another haircut',conversation_id=first['conversation_id']).json()
    result=send(api,message='can you cancel my pending appointment?',conversation_id=first['conversation_id']).json()
    assert f"#{booked['appointment_id']}" in result['answer']
    assert 'awaiting salon confirmation' in result['answer']
    assert 'cancellation is currently unsupported' in result['answer']
    assert result['confirmation']['id']==pending['confirmation']['id']
    with sessions() as db: assert db.get(Appointment,booked['appointment_id']).status=='pending'


def test_appointment_serialization_marks_utc_and_exposes_salon_timezone(monkeypatch):
    from app.schemas.appointment import AppointmentOut
    from zoneinfo import ZoneInfo
    monkeypatch.setattr(settings,'salon_timezone','America/New_York')
    appointment=AppointmentOut(id=144,customer_name='Test',customer_email='test@example.com',service_id=1,start_time=datetime(2026,10,7,15),status='pending')
    output=appointment.model_dump(mode='json')
    assert output['start_time']=='2026-10-07T15:00:00Z'
    assert output['salon_timezone']=='America/New_York'
    local=datetime.fromisoformat(output['start_time'].replace('Z','+00:00')).astimezone(ZoneInfo(output['salon_timezone']))
    assert local.strftime('%Y-%m-%d %H:%M')=='2026-10-07 11:00'
    assert output['status']=='pending'


@pytest.mark.parametrize('day,opening,closing',[('2027-01-07','2027-01-07T13:00:00','2027-01-08T00:00:00'),('2027-07-07','2027-07-07T12:00:00','2027-07-07T23:00:00')])
def test_salon_day_bounds_follow_winter_and_summer_offsets(setup,day,opening,closing):
    from app.services.booking_hours import business_day_bounds
    from datetime import date
    opened,closed=business_day_bounds(date.fromisoformat(day))
    assert opened.isoformat()==opening and closed.isoformat()==closing


@pytest.mark.parametrize('duration,last_time',[(30,'18:30'),(90,'17:30')])
@pytest.mark.parametrize('day',['2027-01-07','2027-07-07'])
def test_availability_and_chat_share_local_hours_and_duration(setup,duration,last_time,day):
    from zoneinfo import ZoneInfo
    api,sessions,model,_=setup
    with sessions() as db:
        db.get(Service,1).duration_minutes=duration
        db.commit()
    response=api.get('/api/appointments/availability',params={'service_id':1,'booking_date':day})
    assert response.status_code==200,response.text
    data=response.json()
    assert data['timezone']=='America/New_York'
    assert data['slots'][0]['start_time']=='08:00'
    assert data['slots'][-1]['start_time']==last_time
    assert all(slot['available'] for slot in data['slots'])
    model.return_value=chat.Extracted(intent='booking',service_id=1,booking_date=day,booking_time=last_time)
    reply=offer(api)
    offered=datetime.fromisoformat(reply['confirmation']['start_utc'])
    manual=datetime.fromisoformat(data['slots'][-1]['start_utc'].replace('Z','+00:00'))
    assert offered==manual
    assert offered.astimezone(ZoneInfo('America/New_York')).strftime('%H:%M')==last_time
    # Manual UI submits the explicit UTC timestamp supplied by availability.
    booked=api.post('/api/appointments/me',json={'service_id':1,'start_time':data['slots'][-1]['start_utc']})
    assert booked.status_code==200,booked.text
    assert booked.json()['start_time']==data['slots'][-1]['start_utc']
    changed=api.get('/api/appointments/availability',params={'service_id':1,'booking_date':day}).json()
    assert changed['slots'][-1]['available'] is False
    confirmation=api.post('/api/chat',json=confirm_payload(reply)).json()
    assert confirmation['appointment_id'] is None
    with sessions() as db: assert db.query(Appointment).count()==1


@pytest.mark.parametrize('duration,clock,allowed',[(30,'08:00',True),(30,'07:30',False),(30,'18:30',True),(30,'19:00',False),(90,'17:30',True),(90,'18:00',False)])
def test_manual_creation_enforces_entire_service_inside_local_hours(setup,duration,clock,allowed):
    from zoneinfo import ZoneInfo
    api,sessions,_,_=setup
    with sessions() as db:
        db.get(Service,1).duration_minutes=duration
        db.commit()
    local=datetime.fromisoformat('2027-07-07T'+clock).replace(tzinfo=ZoneInfo('America/New_York'))
    response=api.post('/api/appointments/me',json={'service_id':1,'start_time':local.astimezone(timezone.utc).isoformat()})
    assert response.status_code==(200 if allowed else 400),response.text
    with sessions() as db: assert db.query(Appointment).count()==(1 if allowed else 0)


def test_policy_endpoint_and_chat_hours_match(setup):
    api,_,model,_=setup
    policy=api.get('/api/appointments/booking-policy').json()
    assert policy=={'opening_time':'08:00','closing_time':'19:00','timezone':'America/New_York'}
    model.return_value=chat.Extracted(intent='hours')
    answer=send(api,message='What are your booking hours?').json()['answer']
    assert '08:00' in answer and '19:00' in answer and policy['timezone'] in answer
    assert 'UTC' not in answer
