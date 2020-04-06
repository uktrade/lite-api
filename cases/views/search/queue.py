class SearchQueue:
    """
    A SearchQueue is a representation of a Queue or a system Queue 😀
    """

    def __init__(self, id, name, cases):
        self.id = id
        self.name = name
        self.cases = cases

    @classmethod
    def from_queue(cls, queue) -> "SearchQueue":
        return cls(id=queue.id, name=queue.name, cases=queue.cases)
