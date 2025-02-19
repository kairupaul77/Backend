from flask import jsonify

def paginate(query, model, page=1, per_page=10):
    """
    Paginate the results of a query and return the results as a JSON response.
    
    Args:
    - query: The query object to paginate
    - model: The SQLAlchemy model to count the total number of results
    - page: The page number (default is 1)
    - per_page: The number of items per page (default is 10)
    
    Returns:
    - A JSON response containing paginated data
    """
    # Calculate the total number of results
    total = query.count()

    # Handle invalid page number (e.g., if page is larger than total pages)
    if page < 1:
        page = 1

    # Ensure that we do not ask for more pages than the available pages
    total_pages = (total // per_page) + (1 if total % per_page > 0 else 0)

    if page > total_pages:
        page = total_pages
    
    # Apply pagination to the query
    results = query.paginate(page, per_page, False)

    # Serialize the results
    items = [item.to_dict() for item in results.items]  # assuming `to_dict` exists on model
    
    # Return a paginated response
    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,  # total number of pages
        'items': items
    })