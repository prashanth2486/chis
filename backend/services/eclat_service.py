import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

def compute_frequent_patterns(transactions: list[str], min_support: float = 0.04, min_confidence: float = 0.5):
    """
    Computes frequent patterns and strong rules from a list of transactions using mlxtend.
    
    Args:
        transactions: List of strings, where each string is a comma-separated list of items.
        min_support: Minimum support threshold (default 0.04 -> 4%)
        min_confidence: Minimum confidence threshold (default 0.5 -> 50%)
        
    Returns:
        frequent_items_dict: Dictionary mapping frequent string combinations to their support string.
        rules_list: List of tuples (X, Y, Confidence).
    """
    if not transactions:
        return {}, []

    # Parse transactions into lists of items
    dataset = []
    for t in transactions:
        if t:
            items = [item.strip() for item in str(t).split(',') if item.strip()]
            dataset.append(items)

    if not dataset:
        return {}, []

    # One-hot encoding using pandas
    all_items = set(item for sublist in dataset for item in sublist)
    
    # Create an empty dataframe with correct structure
    df_data = []
    for transaction in dataset:
        row = {item: False for item in all_items}
        for item in transaction:
            row[item] = True
        df_data.append(row)
        
    df = pd.DataFrame(df_data)

    # Calculate frequent itemsets using apriori
    try:
        frequent_itemsets = apriori(df, min_support=min_support, use_colnames=True)
    except Exception as e:
        return {}, []

    if frequent_itemsets.empty:
        return {}, []

    # Convert frequent itemsets to format expected by UI
    frequent_items_dict = {}
    for idx, row in frequent_itemsets.iterrows():
        items = list(row['itemsets'])
        items.sort()
        key = ','.join(items)
        
        # Calculate raw support count
        support_count = int(row['support'] * len(dataset))
        # The legacy C# app returned a string of indices here: "0,1,5" 
        # We can approximate this or just return the support count for simplicity.
        # Let's return the string of row indices where these items were present.
        
        matching_rows = df[list(row['itemsets'])].all(axis=1)
        indices = matching_rows[matching_rows].index.tolist()
        frequent_items_dict[key] = ','.join(map(str, indices))

    # Generate association rules
    try:
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    except Exception as e:
        return frequent_items_dict, []

    rules_list = []
    if not rules.empty:
        for idx, row in rules.iterrows():
            antecedents = list(row['antecedents'])
            consequents = list(row['consequents'])
            antecedents.sort()
            consequents.sort()
            
            x = ','.join(antecedents)
            y = ','.join(consequents)
            conf = row['confidence']
            rules_list.append((x, y, conf))

    # Clean up duplicate rules or sort them
    rules_list = sorted(set(rules_list), key=lambda x: x[2], reverse=True)

    return frequent_items_dict, rules_list
