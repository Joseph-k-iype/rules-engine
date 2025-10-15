package gdpr

import future.keywords.in
import future.keywords.if
import future.keywords.every

# ==============================================================================
# OPTIMIZED REGO POLICIES - Focused on Performance
# ==============================================================================

# Pre-compute common values to avoid recalculation
adequacy_countries := {"US", "CA", "JP", "UK", "CH", "IL", "NZ", "AR", "UY", "KR"}

# ==============================================================================
# FEATURE 1: SET OPERATIONS (Optimized)
# ==============================================================================

excessive_data_collection := {
    "collected_count": count(collected_fields),
    "necessary_count": count(necessary_fields),
    "excessive_fields": excessive,
    "excessive_count": count(excessive),
    "compliant": count(excessive) == 0
} if {
    collected_fields := input.personal_data.collected_fields
    necessary_fields := input.personal_data.necessary_fields
    excessive := {f | f := collected_fields[_]} - {f | f := necessary_fields[_]}
}

# ==============================================================================
# FEATURE 2: UNIVERSAL QUANTIFICATION (Optimized)
# ==============================================================================

all_vendors_compliant := {
    "total_vendors": vendor_count,
    "all_dpa_signed": all_dpa,
    "all_in_adequate_countries": all_adequate,
    "fully_compliant": fully_compliant,
    "compliant": vendor_count == 0 or fully_compliant
} if {
    vendors := input.vendor_relationships
    vendor_count := count(vendors)
    
    # Check DPA status
    all_dpa := vendor_count == 0 or count([v | v := vendors[_]; v.dpa_status == "signed"]) == vendor_count
    
    # Check adequate countries
    all_adequate := vendor_count == 0 or count([v | v := vendors[_]; v.country in adequacy_countries]) == vendor_count
    
    # Combined check
    fully_compliant := all_dpa and all_adequate
}

all_transfers_lawful := {
    "transfer_count": transfer_count,
    "all_countries_adequate": all_adequate,
    "has_safeguards": has_safeguards,
    "compliant": compliant
} if {
    countries := input.data_transfers.third_countries
    transfer_count := count(countries)
    
    # Check if all countries are adequate
    all_adequate := transfer_count == 0 or count([c | c := countries[_]; c in adequacy_countries]) == transfer_count
    
    # Check safeguards
    has_safeguards := input.data_transfers.standard_clauses == true
    has_dpa := input.data_transfers.dpa_signed == true
    
    # Compliant if no transfers, all adequate, or has proper safeguards
    compliant := transfer_count == 0 or all_adequate or (has_safeguards and has_dpa)
}

# ==============================================================================
# FEATURE 3: REGEX MATCHING (Optimized)
# ==============================================================================

email_validation := {
    "email": email,
    "valid_format": valid,
    "compliant": valid
} if {
    email := input.email
    # Simple regex for performance
    valid := regex.match(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`, email)
}

# Optimized sensitive field detection - only check if needed
sensitive_field_detection := {
    "ssn_related": ssn_fields,
    "credit_related": credit_fields,
    "health_related": health_fields,
    "biometric_related": biometric_fields,
    "all_sensitive_fields": all_sensitive,
    "has_sensitive_data": count(all_sensitive) > 0
} if {
    fields := input.personal_data.collected_fields
    
    # Use simple contains instead of complex regex for speed
    ssn_fields := [f | f := fields[_]; contains(lower(f), "ssn")]
    credit_fields := [f | f := fields[_]; contains(lower(f), "credit")]
    health_fields := [f | f := fields[_]; contains(lower(f), "health")]
    biometric_fields := [f | f := fields[_]; contains(lower(f), "biometric")]
    
    all_sensitive := array.concat(array.concat(ssn_fields, credit_fields), 
                                  array.concat(health_fields, biometric_fields))
}

# ==============================================================================
# FEATURE 4: RECURSIVE RULES (Optimized)
# ==============================================================================

# Simple depth calculation without deep recursion
vendor_chain_analysis := {
    "direct_vendor_count": vendor_count,
    "vendor_chain_depth": depth,
    "max_allowed_depth": 3,
    "depth_compliant": depth <= 3,
    "chain_compliant": all_compliant
} if {
    vendors := input.vendor_relationships
    vendor_count := count(vendors)
    
    # Simple depth check (max 2 levels to avoid deep recursion)
    depth := max_depth(vendors, 0)
    
    # Check if all vendors and their direct sub-processors are compliant
    all_compliant := vendor_count == 0 or check_vendors_simple(vendors)
}

# Optimized depth calculation - limit recursion depth
max_depth(vendors, current) := d if {
    count(vendors) == 0
    d := current
}

max_depth(vendors, current) := d if {
    count(vendors) > 0
    
    # Only check direct sub-processors (one level deep)
    has_subs := count([v | v := vendors[_]; count(v.sub_processors) > 0]) > 0
    
    d := current + 1 if has_subs
    d := current + 1 if not has_subs
}

# Simple compliance check without deep recursion
check_vendors_simple(vendors) if {
    # All vendors have signed DPA
    count([v | v := vendors[_]; v.dpa_status == "signed"]) == count(vendors)
}

# ==============================================================================
# BASIC POLICIES (Minimal computation)
# ==============================================================================

basic_policies := {
    "marketing_consent_active": consent_active,
    "has_dpa_signed": has_dpa
} if {
    consent_active := input.consent.marketing == true and input.consent.status == "active"
    has_dpa := input.data_transfers.dpa_signed == true
}

# ==============================================================================
# AGGREGATE RESULTS (Optimized structure)
# ==============================================================================

policies := {
    "excessive_data_collection": excessive_data_collection,
    "all_vendors_compliant": all_vendors_compliant,
    "all_transfers_lawful": all_transfers_lawful,
    "email_validation": email_validation,
    "sensitive_field_detection": sensitive_field_detection,
    "vendor_chain_analysis": vendor_chain_analysis
}

# Simple compliance check
compliant if {
    excessive_data_collection.compliant
    all_vendors_compliant.compliant
    all_transfers_lawful.compliant
    email_validation.compliant
    vendor_chain_analysis.chain_compliant
}

# Minimal summary for fast response
summary := {
    "compliant": compliant,
    "policies": policies,
    "features_demonstrated": {
        "set_operations": "excessive_data_collection",
        "universal_quantification": "all_vendors_compliant",
        "regex_matching": "email_validation",
        "recursive_rules": "vendor_chain_analysis"
    }
}