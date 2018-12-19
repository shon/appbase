from nose.tools import assert_raises
import appbase.context as context
from appbase.errors import AccessDenied
from appbase.helpers import match_all_roles, match_any_role


def test_match_roles():
    context.current.groups = ['admin', 'editor']
    match_all_roles(['admin', 'editor'])
    match_all_roles(['editor'])
    match_any_role(['editor', 'publisher'])
    with assert_raises(AccessDenied):
        match_all_roles(['publisher'])
    with assert_raises(AccessDenied):
        match_any_role(['publisher'])

    context.current.groups = ['editor', 'article:999:publish', 'series:3:publish']
    match_all_roles(['series:{series_id}:publish', 'editor'], series_id=3)
    match_any_role(
        ['article:{article_id}:publish', 'series:{series_id}:publish'],
        series_id=3, article_id=55
        )
    with assert_raises(AccessDenied):
        match_all_roles(['series:{series_id}:publish', 'editor'], series_id=5)
    with assert_raises(AccessDenied):
        match_all_roles(
            ['article:{article_id}:publish', 'series:{series_id}:publish'],
            series_id=3, article_id=55
            )

