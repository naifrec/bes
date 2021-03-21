"""
Functions to clean up the YouTube video name prior to separating artist name
from track name.

"""
import re

def clean_tracklisting(string):
    """Clean tracklisting in track name: 'A1.', 'A2.', etc """
    result = re.search(r'^([ABCD]{1}[1234]{0,1}\.\s?).*$', string, re.IGNORECASE)
    if result is not None:
        tracklisting = result.groups()[0]
        string = string.replace(tracklisting, '')
    return string


def clean_label_or_catalog_number(string):
    """Clean label or catalog ID: '[TMZ12006]', '[Kalahari Oyster Cult]' """
    string = string.replace('【', '[')
    string = string.replace('】', ']')
    result = re.search(r'(\[.*\])', string)
    if result is not None:
        label_or_catalog_number = result.groups()[0]
        string = string.replace(label_or_catalog_number, '')
    return string


def clean_premiere_prefix(string):
    """Clean premiere prefix"""
    # looks for strings like "PREMIERE:", "premiere "
    result = re.search(r'(premiere\:?\s)', string, re.IGNORECASE)
    if result is not None:
        prefix = result.groups()[0]
        string = string.replace(prefix, '')
    return string


def clean_parentheses(string):
    """
    There are often additional information between parentheses. While some
    is extra info distracting the search engines, some need not be removed,
    in particular if they contain the substring: 'mix', 'remix', 'edit',
    'rework', 'reshape', 'dub', 'version'.

    """
    allowed_names = ('mix', 'remix', 'edit', 'rework', 'reshape', 'dub', 'version')
    groups = re.findall(r'(\([^\)]*\))', string)
    if groups:
        if len(groups) > 1:
            # additional parentheses usually contains junk info
            for group in groups[1:]:
                string = string.replace(group, '').strip()
        else:
            # remove parenthesis only if does not contain any allowed name
            group = groups[0].lower()
            if not any(name in group for name in allowed_names):
                string = string.replace(group, '').strip()
    return string


def clean(string):
    """Call all clean functions in sequence"""
    for function in [clean_tracklisting, clean_label_or_catalog_number,
                     clean_premiere_prefix, clean_parentheses]:
        string = function(string)
    return string.strip()
