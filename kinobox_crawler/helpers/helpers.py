def should_abort_request(req):
    if req.resource_type == 'image':
        return True

    return False
