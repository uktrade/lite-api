def queue_serializer(queues):
    return [{
        "id": queue.id,
        "name": queue.name,
        "case_count": queue.cases.count()
    } for queue in queues]
