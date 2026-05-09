from collections import Counter
from typing import List

import matplotlib.pyplot as plt

import config
from data_loader import DataLoader
from model import Issue


class LabelActivityAnalysis:
    """
    Analyzes issue activity by label.
    Can focus on a specific label if --label is provided.
    """

    def __init__(self):
        self.LABEL = config.get_parameter('label')

    def run(self):
        #load all issues from the dataset
        issues: List[Issue] = DataLoader().get_issues()

        #filter issues if a specific label was requested
        if self.LABEL:
            filtered_issues = [issue for issue in issues if self.LABEL in issue.labels]
        else:
            filtered_issues = issues

        #handle case where no issues match the requested label
        if not filtered_issues:
            print(f'No issues found for label: {self.LABEL}')
            return

        print(f'\nFound {len(filtered_issues)} matching issues.\n')

        #count occurrences of each event type across matching issues
        label_counter = Counter()
        event_counter = Counter()

        for issue in filtered_issues:
            for label in issue.labels:
                label_counter[label] += 1
            for event in issue.events:
                event_counter[event.event_type] += 1

        print('Top labels in filtered issues:')
        for label, count in label_counter.most_common(10):
            print(f'  {label}: {count}')

        print('\nTop event types in filtered issues:')
        for event_type, count in event_counter.most_common(10):
            print(f'  {event_type}: {count}')

        top_items = event_counter.most_common(10)
        names = [item[0] for item in top_items]
        values = [item[1] for item in top_items]

        #generate visualization of event type frequency
        plt.figure(figsize=(12, 6))
        plt.bar(names, values)
        plt.title(f'Event Types for Label: {self.LABEL}' if self.LABEL else 'Top Event Types Across All Issues')
        plt.xlabel('Event Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
