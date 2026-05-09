import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import config
from model import Issue

from label_activity_analysis import LabelActivityAnalysis
from contributor_activity_analysis import ContributorActivityAnalysis
from issue_trend_analysis import IssueTrendAnalysis
from example_analysis import ExampleAnalysis


def make_issue(
    number,
    creator,
    labels,
    state="open",
    created_date="2024-09-01T00:00:00+00:00",
    events=None
):
    return Issue({
        "url": f"https://github.com/example/project/issues/{number}",
        "creator": creator,
        "labels": labels,
        "state": state,
        "assignees": [],
        "title": f"Issue {number}",
        "text": "Body",
        "number": number,
        "created_date": created_date,
        "updated_date": created_date,
        "timeline_url": "timeline",
        "events": events or []
    })


class FakeDataLoader:
    def __init__(self, issues):
        self.issues = issues

    def get_issues(self):
        return self.issues


class TestAnalyses(unittest.TestCase):

    def setUp(self):
        config._config = {}
        self.issues = [
            make_issue(
                1,
                "alice",
                ["Bug", "Needs Triage"],
                "open",
                "2024-09-01T00:00:00+00:00",
                [
                    {
                        "event_type": "labeled",
                        "author": "alice",
                        "event_date": "2024-09-01T00:01:00+00:00",
                        "label": "Bug"
                    },
                    {
                        "event_type": "commented",
                        "author": "bob",
                        "event_date": "2024-09-01T00:02:00+00:00",
                        "comment": "comment"
                    }
                ]
            ),
            make_issue(
                2,
                "bob",
                ["Documentation"],
                "closed",
                "2024-10-01T00:00:00+00:00",
                [
                    {
                        "event_type": "closed",
                        "author": "bob",
                        "event_date": "2024-10-01T00:02:00+00:00"
                    }
                ]
            )
        ]

    def tearDown(self):
        config._config = {}

    @patch("label_activity_analysis.plt.show")
    @patch("label_activity_analysis.DataLoader")
    def test_label_activity_all_labels(self, mock_loader_class, mock_show):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"label": None}

        output = io.StringIO()
        with redirect_stdout(output):
            LabelActivityAnalysis().run()

        text = output.getvalue()
        self.assertIn("Found 2 matching issues", text)
        self.assertIn("Bug", text)
        self.assertTrue(mock_show.called)

    @patch("label_activity_analysis.plt.show")
    @patch("label_activity_analysis.DataLoader")
    def test_label_activity_specific_label(self, mock_loader_class, mock_show):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"label": "Bug"}

        output = io.StringIO()
        with redirect_stdout(output):
            LabelActivityAnalysis().run()

        text = output.getvalue()
        self.assertIn("Found 1 matching issues", text)
        self.assertIn("commented", text)
        self.assertTrue(mock_show.called)

    @patch("label_activity_analysis.DataLoader")
    def test_label_activity_no_matching_label(self, mock_loader_class):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"label": "NoSuchLabel"}

        output = io.StringIO()
        with redirect_stdout(output):
            LabelActivityAnalysis().run()

        self.assertIn("No issues found for label", output.getvalue())

    @patch("contributor_activity_analysis.plt.show")
    @patch("contributor_activity_analysis.DataLoader")
    def test_contributor_activity_all_users(self, mock_loader_class, mock_show):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"user": None}

        output = io.StringIO()
        with redirect_stdout(output):
            ContributorActivityAnalysis().run()

        text = output.getvalue()
        self.assertIn("Top issue creators", text)
        self.assertIn("alice", text)
        self.assertTrue(mock_show.called)

    @patch("contributor_activity_analysis.plt.show")
    @patch("contributor_activity_analysis.DataLoader")
    def test_contributor_activity_specific_user_with_events(self, mock_loader_class, mock_show):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"user": "bob"}

        output = io.StringIO()
        with redirect_stdout(output):
            ContributorActivityAnalysis().run()

        text = output.getvalue()
        self.assertIn("Contributor: bob", text)
        self.assertIn("Issues created: 1", text)
        self.assertIn("Events authored: 2", text)
        self.assertTrue(mock_show.called)

    @patch("contributor_activity_analysis.DataLoader")
    def test_contributor_activity_no_activity(self, mock_loader_class):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"user": "nobody"}

        output = io.StringIO()
        with redirect_stdout(output):
            ContributorActivityAnalysis().run()

        self.assertIn("No activity found for user", output.getvalue())

    @patch("contributor_activity_analysis.DataLoader")
    def test_contributor_created_issue_but_no_events(self, mock_loader_class):
        issue = make_issue(3, "charlie", ["Bug"], "open", events=[])
        mock_loader_class.return_value = FakeDataLoader([issue])
        config._config = {"user": "charlie"}

        output = io.StringIO()
        with redirect_stdout(output):
            ContributorActivityAnalysis().run()

        self.assertIn("created issues but has no authored events", output.getvalue())

    @patch("issue_trend_analysis.plt.show")
    @patch("issue_trend_analysis.DataLoader")
    def test_issue_trend_analysis_with_issues(self, mock_loader_class, mock_show):
        mock_loader_class.return_value = FakeDataLoader(self.issues)

        output = io.StringIO()
        with redirect_stdout(output):
            IssueTrendAnalysis().run()

        text = output.getvalue()
        self.assertIn("Overall Issue Trends", text)
        self.assertIn("Total issues: 2", text)
        self.assertIn("Open issues: 1", text)
        self.assertIn("Closed issues: 1", text)
        self.assertTrue(mock_show.called)

    @patch("issue_trend_analysis.DataLoader")
    def test_issue_trend_analysis_empty_dataset(self, mock_loader_class):
        mock_loader_class.return_value = FakeDataLoader([])

        output = io.StringIO()
        with redirect_stdout(output):
            IssueTrendAnalysis().run()

        self.assertIn("No issues found in dataset", output.getvalue())

    @patch("issue_trend_analysis.plt.show")
    @patch("issue_trend_analysis.DataLoader")
    def test_issue_trend_analysis_no_labels(self, mock_loader_class, mock_show):
        issue = make_issue(4, "alice", [], "open")
        mock_loader_class.return_value = FakeDataLoader([issue])

        output = io.StringIO()
        with redirect_stdout(output):
            IssueTrendAnalysis().run()

        self.assertIn("Total issues: 1", output.getvalue())
        self.assertFalse(mock_show.called)

    @patch("example_analysis.plt.show")
    @patch("example_analysis.DataLoader")
    def test_example_analysis_all_users(self, mock_loader_class, mock_show):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"user": None}

        output = io.StringIO()
        with redirect_stdout(output):
            ExampleAnalysis().run()

        self.assertIn("Found 3 events across 2 issues", output.getvalue())
        self.assertTrue(mock_show.called)

    @patch("example_analysis.plt.show")
    @patch("example_analysis.DataLoader")
    def test_example_analysis_specific_user(self, mock_loader_class, mock_show):
        mock_loader_class.return_value = FakeDataLoader(self.issues)
        config._config = {"user": "bob"}

        output = io.StringIO()
        with redirect_stdout(output):
            ExampleAnalysis().run()

        self.assertIn("Found 2 events across 2 issues for bob", output.getvalue())
        self.assertTrue(mock_show.called)


if __name__ == "__main__":
    unittest.main()
