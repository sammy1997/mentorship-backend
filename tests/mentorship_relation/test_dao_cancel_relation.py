from datetime import datetime, timedelta

from app.api.dao.mentorship_relation import MentorshipRelationDAO
from app.utils.enum_utils import MentorshipRelationState
from app.database.models.mentorship_relation import MentorshipRelationModel
from app.database.models.user import UserModel
from app.database.sqlalchemy_extension import db
from tests.base_test_case import BaseTestCase
from tests.test_data import user1, user2


# TODO test when a user tries to cancel a relation where this user is not involved

class TestMentorshipRelationListingDAO(BaseTestCase):

    # Setup consists of adding 2 users into the database
    # User 1 is the mentorship relation requester = action user
    # User 2 is the receiver
    def setUp(self):
        super(TestMentorshipRelationListingDAO, self).setUp()

        self.first_user = UserModel(
            name=user1['name'],
            email=user1['email'],
            username=user1['username'],
            password=user1['password'],
            terms_and_conditions_checked=user1['terms_and_conditions_checked']
        )
        self.second_user = UserModel(
            name=user2['name'],
            email=user2['email'],
            username=user2['username'],
            password=user2['password'],
            terms_and_conditions_checked=user2['terms_and_conditions_checked']
        )

        # making sure both are available to be mentor or mentee
        self.first_user.need_mentoring = True
        self.first_user.available_to_mentor = True
        self.second_user.need_mentoring = True
        self.second_user.available_to_mentor = True

        self.notes_example = 'description of a good mentorship relation'

        self.now_datetime = datetime.now()
        self.end_date_example = self.now_datetime + timedelta(weeks=5)

        db.session.add(self.first_user)
        db.session.add(self.second_user)
        db.session.commit()

        # create new mentorship relation

        self.mentorship_relation = MentorshipRelationModel(
            action_user_id=self.first_user.id,
            mentor_user=self.first_user,
            mentee_user=self.second_user,
            creation_date=self.now_datetime.timestamp(),
            end_date=self.end_date_example.timestamp(),
            state=MentorshipRelationState.PENDING,
            notes=self.notes_example
        )

        db.session.add(self.mentorship_relation)
        db.session.commit()

    def test_dao_cancel_non_existing_mentorship_request(self):
        DAO = MentorshipRelationDAO()

        result = DAO.cancel_relation(self.first_user.id, 123)

        self.assertEqual(({'message': 'This mentorship relation request does not exist.'}, 404), result)
        self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)

    def test_dao_sender_does_not_exist_mentorship_request(self):
        DAO = MentorshipRelationDAO()

        result = DAO.cancel_relation(123, self.mentorship_relation.id)

        self.assertEqual(({'message': 'User does not exist.'}, 404), result)
        self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)

    def test_dao_receiver_cancel_mentorship_request(self):
        self.mentorship_relation.state = MentorshipRelationState.ACCEPTED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        DAO = MentorshipRelationDAO()
        result = DAO.cancel_relation(self.second_user.id, self.mentorship_relation.id)

        self.assertEqual(({'message': 'Mentorship relation was cancelled successfully.'}, 200), result)
        self.assertEqual(MentorshipRelationState.CANCELLED, self.mentorship_relation.state)

    def test_dao_sender_cancel_mentorship_request(self):
        self.mentorship_relation.state = MentorshipRelationState.ACCEPTED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        DAO = MentorshipRelationDAO()
        result = DAO.cancel_relation(self.first_user.id, self.mentorship_relation.id)

        self.assertEqual(({'message': 'Mentorship relation was cancelled successfully.'}, 200), result)
        self.assertEqual(MentorshipRelationState.CANCELLED, self.mentorship_relation.state)

    def test_dao_mentorship_cancel_relation_not_in_accepted_state(self):
        DAO = MentorshipRelationDAO()

        self.mentorship_relation.state = MentorshipRelationState.PENDING
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.cancel_relation(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual(({'message': 'This mentorship relation is not in the accepted state.'}, 400), result)

        self.mentorship_relation.state = MentorshipRelationState.COMPLETED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.cancel_relation(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual(({'message': 'This mentorship relation is not in the accepted state.'}, 400), result)

        self.mentorship_relation.state = MentorshipRelationState.CANCELLED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.cancel_relation(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual(({'message': 'This mentorship relation is not in the accepted state.'}, 400), result)

        self.mentorship_relation.state = MentorshipRelationState.REJECTED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.cancel_relation(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual(({'message': 'This mentorship relation is not in the accepted state.'}, 400), result)