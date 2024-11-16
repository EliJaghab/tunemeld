from core.cache import CloudflareKV

# ...existing code...

def handle_graph_data(request, genre_name):
    kv_store = CloudflareKV()
    key = f"graph_data_{genre_name}"
    
    # Try to get the existing data
    graph_data = kv_store.get_kv_entry(key)
    
    if graph_data is None:
        # If it doesn't exist, insert new data
        new_data = generate_graph_data(genre_name)  # Assuming this function generates the graph data
        kv_store.put_kv_entry(key, new_data)
        graph_data = new_data
    
    return graph_data

# ...existing code...