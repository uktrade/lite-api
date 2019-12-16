from conf.pagination import MaxPageNumberPagination


class GoodListPaginator(MaxPageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 50
