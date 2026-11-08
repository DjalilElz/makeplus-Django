from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Same 20-per-page default as before, but a client may ask for bigger pages
    with ?page_size= (capped). The mobile app loads a whole programme
    (100+ sessions) in one request instead of six sequential round trips.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 500
