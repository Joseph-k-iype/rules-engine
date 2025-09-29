package legislation.rules

import rego.v1

# ===================================================================
# RULE QUERY ENGINE - Flexible filtering and retrieval system
# ===================================================================

# Get all rules (default if no filters applied)
default rules_result := input.rules

# Filter rules by country
rules_by_country[country] := filtered_rules if {
    some country
    countries := {c | some rule in input.rules; some c in rule.applicable_countries}
    country in countries
    filtered_rules := [rule | some rule in input.rules; country in rule.applicable_countries]
}

# Filter rules by data category
rules_by_data_category[category] := filtered_rules if {
    some category
    categories := {c | some rule in input.rules; some c in rule.data_categories}
    category in categories
    filtered_rules := [rule | some rule in input.rules; category in rule.data_categories]
}

# Filter rules by processing purpose
rules_by_purpose[purpose] := filtered_rules if {
    some purpose
    purposes := {p | some rule in input.rules; some p in rule.processing_purposes}
    purpose in purposes
    filtered_rules := [rule | some rule in input.rules; purpose in rule.processing_purposes]
}

# Filter rules by action category
rules_by_action_category[category] := filtered_rules if {
    some category
    categories := {c | some rule in input.rules; some action in rule.actions; c := action.action_category}
    category in categories
    filtered_rules := [rule | 
        some rule in input.rules
        some action in rule.actions
        action.action_category == category
    ]
}

# Filter rules by action type
rules_by_action_type[action_type] := filtered_rules if {
    some action_type
    types := {t | some rule in input.rules; some action in rule.actions; t := action.action_type}
    action_type in types
    filtered_rules := [rule | 
        some rule in input.rules
        some action in rule.actions
        action.action_type == action_type
    ]
}

# Filter rules by source article
rules_by_source[source] := filtered_rules if {
    some source
    sources := {s | some rule in input.rules; s := rule.source_article}
    source in sources
    filtered_rules := [rule | some rule in input.rules; rule.source_article == source]
}

# Filter rules by impacted role
rules_by_role[role] := filtered_rules if {
    some role
    roles := {r | some rule in input.rules; r := rule.primary_impacted_role}
    role in roles
    filtered_rules := [rule | some rule in input.rules; rule.primary_impacted_role == role]
}

# ===================================================================
# COMBINED FILTERS - Query with multiple criteria
# ===================================================================

# Filter by country AND data category
rules_by_country_and_data_category[query_key] := filtered_rules if {
    some country, data_category
    query_key := sprintf("%s_%s", [country, data_category])
    filtered_rules := [rule | 
        some rule in input.rules
        country in rule.applicable_countries
        data_category in rule.data_categories
    ]
}

# Filter by country AND purpose
rules_by_country_and_purpose[query_key] := filtered_rules if {
    some country, purpose
    query_key := sprintf("%s_%s", [country, purpose])
    filtered_rules := [rule | 
        some rule in input.rules
        country in rule.applicable_countries
        purpose in rule.processing_purposes
    ]
}

# Filter by data category AND action category
rules_by_data_and_action_category[query_key] := filtered_rules if {
    some data_category, action_category
    query_key := sprintf("%s_%s", [data_category, action_category])
    filtered_rules := [rule | 
        some rule in input.rules
        data_category in rule.data_categories
        some action in rule.actions
        action.action_category == action_category
    ]
}

# Filter by purpose AND action type
rules_by_purpose_and_action_type[query_key] := filtered_rules if {
    some purpose, action_type
    query_key := sprintf("%s_%s", [purpose, action_type])
    filtered_rules := [rule | 
        some rule in input.rules
        purpose in rule.processing_purposes
        some action in rule.actions
        action.action_type == action_type
    ]
}

# ===================================================================
# DYNAMIC QUERY SYSTEM - Query with input parameters
# ===================================================================

# Query rules based on input filters
query_rules := filtered_rules if {
    input.query
    filtered_rules := apply_query_filters(input.rules, input.query)
}

# Apply multiple filters based on query parameters
apply_query_filters(rules, query) := filtered_rules if {
    # Start with all rules
    step1 := rules
    
    # Apply country filter if specified
    step2 := filter_by_country(step1, query.country) if query.country
    step2 := step1 if not query.country
    
    # Apply data category filter if specified
    step3 := filter_by_data_category(step2, query.data_category) if query.data_category
    step3 := step2 if not query.data_category
    
    # Apply purpose filter if specified
    step4 := filter_by_purpose(step3, query.purpose) if query.purpose
    step4 := step3 if not query.purpose
    
    # Apply action category filter if specified
    step5 := filter_by_action_category(step4, query.action_category) if query.action_category
    step5 := step4 if not query.action_category
    
    # Apply action type filter if specified
    step6 := filter_by_action_type(step5, query.action_type) if query.action_type
    step6 := step5 if not query.action_type
    
    # Apply role filter if specified
    step7 := filter_by_role(step6, query.role) if query.role
    step7 := step6 if not query.role
    
    # Apply source filter if specified
    filtered_rules := filter_by_source(step7, query.source) if query.source
    filtered_rules := step7 if not query.source
}

# Helper functions for dynamic filtering
filter_by_country(rules, country) := [rule | some rule in rules; country in rule.applicable_countries]
filter_by_data_category(rules, category) := [rule | some rule in rules; category in rule.data_categories]
filter_by_purpose(rules, purpose) := [rule | some rule in rules; purpose in rule.processing_purposes]
filter_by_role(rules, role) := [rule | some rule in rules; rule.primary_impacted_role == role]
filter_by_source(rules, source) := [rule | some rule in rules; rule.source_article == source]

filter_by_action_category(rules, category) := [rule | 
    some rule in rules
    some action in rule.actions
    action.action_category == category
]

filter_by_action_type(rules, action_type) := [rule | 
    some rule in rules
    some action in rule.actions
    action.action_type == action_type
]

# ===================================================================
# EXTRACT COMPONENTS - Get specific parts from filtered rules
# ===================================================================

# Extract all actions from query results
actions_from_query := actions if {
    rules := query_rules
    actions := [action | some rule in rules; some action in rule.actions]
}

actions_from_query := actions if {
    not input.query
    actions := [action | some rule in input.rules; some action in rule.actions]
}

# Extract all conditions from query results
conditions_from_query := conditions if {
    rules := query_rules
    conditions := [condition | 
        some rule in rules
        rule.condition_logic
        some condition in rule.condition_logic.conditions
    ]
}

conditions_from_query := conditions if {
    not input.query
    conditions := [condition | 
        some rule in input.rules
        rule.condition_logic
        some condition in rule.condition_logic.conditions
    ]
}

# Extract organizational actions only
organizational_actions := [action | 
    some action in actions_from_query
    action.action_category == "organizational"
]

# Extract individual actions only
individual_actions := [action | 
    some action in actions_from_query
    action.action_category == "individual"
]

# ===================================================================
# AGGREGATION AND STATISTICS
# ===================================================================

# Get unique values for different dimensions
unique_countries := {country | some rule in input.rules; some country in rule.applicable_countries}
unique_data_categories := {category | some rule in input.rules; some category in rule.data_categories}
unique_purposes := {purpose | some rule in input.rules; some purpose in rule.processing_purposes}
unique_action_categories := {category | some rule in input.rules; some action in rule.actions; category := action.action_category}
unique_action_types := {action_type | some rule in input.rules; some action in rule.actions; action_type := action.action_type}
unique_roles := {role | some rule in input.rules; role := rule.primary_impacted_role}
unique_sources := {source | some rule in input.rules; source := rule.source_article}

# Count statistics
stats := {
    "total_rules": count(input.rules),
    "total_actions": count(actions_from_query),
    "total_conditions": count(conditions_from_query),
    "organizational_actions_count": count(organizational_actions),
    "individual_actions_count": count(individual_actions),
    "unique_countries_count": count(unique_countries),
    "unique_data_categories_count": count(unique_data_categories),
    "unique_purposes_count": count(unique_purposes),
    "unique_action_types_count": count(unique_action_types)
}

# ===================================================================
# CONDITION EVALUATION SYSTEM
# ===================================================================

# Check if rules apply to given context
applicable_rules := rules if {
    input.context
    rules := [rule | 
        some rule in query_rules
        evaluate_rule_conditions(rule, input.context)
    ]
}

applicable_rules := rules if {
    input.context
    not input.query
    rules := [rule | 
        some rule in input.rules
        evaluate_rule_conditions(rule, input.context)
    ]
}

# Evaluate if a rule's conditions match the context
evaluate_rule_conditions(rule, context) if {
    rule.condition_logic
    evaluate_condition_logic(rule.condition_logic, context)
}

evaluate_rule_conditions(rule, context) if {
    not rule.condition_logic
    # If no condition logic, rule always applies
}

# Evaluate condition logic against context
evaluate_condition_logic(condition_logic, context) if {
    condition_logic.logic_type == "all"
    every condition in condition_logic.conditions {
        evaluate_condition(condition, context)
    }
}

evaluate_condition_logic(condition_logic, context) if {
    condition_logic.logic_type == "any"
    some condition in condition_logic.conditions
    evaluate_condition(condition, context)
}

evaluate_condition_logic(condition_logic, context) if {
    condition_logic.logic_type == "not"
    count([condition | 
        condition := condition_logic.conditions[_]
        evaluate_condition(condition, context)
    ]) == 0
}

# Individual condition evaluation
evaluate_condition(condition, context) if {
    condition.operator == "equal"
    context[condition.fact] == condition.value
}

evaluate_condition(condition, context) if {
    condition.operator == "not_equal"
    context[condition.fact] != condition.value
}

evaluate_condition(condition, context) if {
    condition.operator == "in"
    context[condition.fact] in condition.value
}

evaluate_condition(condition, context) if {
    condition.operator == "not_in"
    not context[condition.fact] in condition.value
}

evaluate_condition(condition, context) if {
    condition.operator == "contains"
    contains(context[condition.fact], condition.value)
}

evaluate_condition(condition, context) if {
    condition.operator == "greater_than"
    to_number(context[condition.fact]) > to_number(condition.value)
}

evaluate_condition(condition, context) if {
    condition.operator == "less_than"
    to_number(context[condition.fact]) < to_number(condition.value)
}

evaluate_condition(condition, context) if {
    condition.operator == "greater_equal"
    to_number(context[condition.fact]) >= to_number(condition.value)
}

evaluate_condition(condition, context) if {
    condition.operator == "less_equal"
    to_number(context[condition.fact]) <= to_number(condition.value)
}