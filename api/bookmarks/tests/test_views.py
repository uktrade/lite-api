import json
import uuid
from random import choice

import pytest
from parameterized import parameterized
from rest_framework.reverse import reverse

from api.bookmarks.models import Bookmark
from api.bookmarks.tests.factories import BookmarkFactory
from test_helpers.clients import DataTestClient


def bookmarks_url():
    return reverse("bookmarks:bookmarks")


class GetBookmarksTests(DataTestClient):
    @parameterized.expand(
        [
            (
                [
                    [False, "UK", "Country is UK", '{"country":"UK"}'],
                    [False, "DE", "Country is Germany", '{"country":"DE"}'],
                    [False, "US", "Country is USA", '{"country":"US"}'],
                ],
                0,
            ),
            (
                [
                    [False, "UK", "Country is UK", '{"country":"UK"}'],
                    [True, "DE", "Country is Germany", '{"country":"DE"}'],
                    [False, "US", "Country is USA", '{"country":"US"}'],
                ],
                1,
            ),
            (
                [
                    [True, "UK", "Country is UK", '{"country":"UK"}'],
                    [True, "DE", "Country is Germany", '{"country":"DE"}'],
                    [True, "US", "Country is USA", '{"country":"US"}'],
                ],
                3,
            ),
        ]
    )
    def test_get_bookmarks(self, saved_bookmarks, users_bookmark_count):
        users = self.add_users()
        for bookmark in saved_bookmarks:
            for_current_user, filter_name, filter_desc, filter_json = bookmark
            user = self.gov_user if for_current_user else choice(users)
            bookmark = Bookmark(user=user, name=filter_name, description=filter_desc, filter_json=filter_json)
            bookmark.save()

        response = self.client.get(bookmarks_url(), **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        user_bookmarks = response.json()["user"]
        self.assertTrue(len(user_bookmarks) == users_bookmark_count)

    @parameterized.expand(
        (
            ["Full filter", "Country is UK", {"country": "UK"}],
            ["Empty filter", "Country is Germany", {}],
            ["No description", "", {"country": "US"}],
        )
    )
    def test_add_bookmark_CREATED(self, name, description, filter_json):
        data = {"name": name, "description": description, "filter_json": filter_json}
        response = self.client.post(bookmarks_url(), data, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 201)

        new_bookmark = response.json()

        self.assertEqual(new_bookmark["name"], name)
        self.assertEqual(new_bookmark["description"], description)
        self.assertEqual(new_bookmark["filter_json"], filter_json)

        created_bookmark = Bookmark.objects.get(
            name=name, description=description, filter_json=filter_json, user=self.gov_user
        )
        self.assertEqual(created_bookmark.name, name)
        self.assertEqual(created_bookmark.description, description)
        self.assertEqual(created_bookmark.filter_json, filter_json)
        self.assertEqual(created_bookmark.user, self.gov_user)

        self.assertEqual(str(created_bookmark.id), new_bookmark["id"])

    @parameterized.expand(
        (
            [{"user": "09efa973-bdb2-415a-a6bc-b2d95895f5d4"}],
            [{"id": "a1026350-b580-4e25-8c2a-17c21370cb32"}],
            [
                {
                    "user": "49e5673a-1e98-4f99-b7fa-7d8e881b0b3b",
                    "id": "4a5ba532-e353-4ec3-a96b-a1f532a29ae6",  # /PS-IGNORE
                }
            ],
        )
    )
    def test_add_bookmark_cannot_override_user_or_id(self, data_overrides):
        data = {"name": "Name", "description": "Description", "filter_json": "{}", **data_overrides}
        response = self.client.post(bookmarks_url(), data, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 201)

        created_bookmark = Bookmark.objects.get(
            name=data["name"], description=data["description"], filter_json=data["filter_json"], user=self.gov_user
        )
        self.assertEqual(created_bookmark.user, self.gov_user)
        if "id" in data_overrides:
            self.assertNotEqual(created_bookmark.id, data_overrides["id"])

    @parameterized.expand(
        (
            "",
            None,
        )
    )
    def test_add_bookmark_failure(self, name):
        data = {
            "name": name,
            "filter_json": {"country": "DE"},
        }
        # Remove missing keys
        response = self.client.post(bookmarks_url(), data, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 400)

    @parameterized.expand(
        (
            [{"name": "UK"}],
            [{"description": "New description"}],
            [{"filter_json": '{"country": "Germany"}'}],
            [{"name": "Spain", "description": "Spanish stuff", "filter_json": '{"country": "Germany"}'}],
        )
    )
    def test_update_bookmark_OK(self, to_update):
        bookmark_id = uuid.uuid4()
        bookmark = Bookmark(id=bookmark_id, user=self.gov_user, name="Temp Name", description="Desc", filter_json="{}")
        bookmark.save()

        data = {"id": bookmark_id, **to_update}
        response = self.client.put(bookmarks_url(), data, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        updated = Bookmark.objects.get(id=bookmark_id)
        self.assertEqual(updated.name, to_update["name"] if "name" in to_update else "Temp Name")
        self.assertEqual(updated.description, to_update["description"] if "description" in to_update else "Desc")
        self.assertEqual(updated.filter_json, to_update["filter_json"] if "filter_json" in to_update else "{}")
        self.assertEqual(updated.user, self.gov_user)

    def test_update_non_existant_bookmark_fails(self):
        data = {"id": uuid.uuid4(), "name": "should fail"}
        response = self.client.put(bookmarks_url(), data, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 404)

    def test_update_bookmark_user_fails(self):
        bookmark_id = uuid.uuid4()
        bookmark = Bookmark(id=bookmark_id, user=self.gov_user, name="Temp Name", description="Desc", filter_json="{}")
        bookmark.save()

        data = {"id": bookmark_id, "user": "49e5673a-1e98-4f99-b7fa-7d8e881b0b3b"}
        response = self.client.put(bookmarks_url(), data, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        updated = Bookmark.objects.get(id=bookmark_id)
        self.assertEqual(updated.user, self.gov_user)

    def test_update_bookmark_for_another_user_fails(self):
        bookmarks, users = self.create_bookmarks()
        other_user_bookmark = [b for b in bookmarks if b.user is not self.gov_user].pop()

        new_name = "Changed Name"
        response = self.client.put(
            bookmarks_url(), {"id": other_user_bookmark.id, "name": new_name}, "json", **self.gov_headers
        )

        self.assertEqual(response.status_code, 404)

        self.assertNotEqual(Bookmark.objects.filter(id=other_user_bookmark.id)[0].name, new_name)

    def test_delete_users_bookmark_OK(self):
        self.create_bookmarks()
        user_bookmark = Bookmark.objects.filter(user=self.gov_user)[0]
        initial_count = Bookmark.objects.count()

        response = self.client.delete(bookmarks_url(), {"id": user_bookmark.id}, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        final_count = Bookmark.objects.count()
        self.assertEqual(final_count, initial_count - 1)

        self.assertFalse(Bookmark.objects.filter(id=user_bookmark.id).exists())

    def test_delete_non_existent_bookmark_fails(self):
        data = {"id": uuid.uuid4()}
        response = self.client.delete(bookmarks_url(), data, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 404)

    def test_delete_other_users_bookmark_fails(self):
        bookmarks, users = self.create_bookmarks()
        other_user_bookmark = [b for b in bookmarks if b.user is not self.gov_user].pop()
        initial_count = Bookmark.objects.count()

        response = self.client.delete(bookmarks_url(), {"id": other_user_bookmark.id}, "json", **self.gov_headers)

        self.assertEqual(response.status_code, 404)

        final_count = Bookmark.objects.count()
        self.assertEqual(final_count, initial_count)
        self.assertTrue(Bookmark.objects.filter(id=other_user_bookmark.id).exists())

    def create_bookmarks(self):
        user = self.gov_user
        users = self.add_users(count=4)
        bookmarks = []
        for i in range(4):
            bookmarks.append(BookmarkFactory(user=user, name=f"current_user {i + 1}"))
            bookmarks.append(BookmarkFactory(user=users[i], name=f"other_user  {i + 1}"))

        return bookmarks, users
