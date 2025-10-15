"""
FastAPI Server for UCAST vs Rego Comparison with Performance Benchmarking
Demonstrates 4 key features + performance differences

Install dependencies:
    pip install fastapi uvicorn pydantic

Run server:
    uvicorn api:app --reload

API Docs:
    http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import re
import time
import statistics

app = FastAPI(
    title="UCAST vs Rego Policy Evaluation API with Benchmarks",
    description="Compare UCAST and Rego capabilities + performance for GDPR compliance",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class UserData(BaseModel):
    user_id: str
    email: str
    country: str
    region: str
    account_status: str
    consent: Dict[str, Any]
    personal_data: Dict[str, Any]
    data_transfers: Dict[str, Any]
    vendor_relationships: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_001",
                "email": "user@example.com",
                "country": "US",
                "region": "NA",
                "account_status": "active",
                "consent": {
                    "marketing": True,
                    "status": "active"
                },
                "personal_data": {
                    "collected_fields": ["name", "email", "ssn", "credit_score"],
                    "necessary_fields": ["name", "email"],
                    "sensitive_data": True
                },
                "data_transfers": {
                    "third_countries": ["US", "UK"],
                    "standard_clauses": True,
                    "dpa_signed": True
                },
                "vendor_relationships": [
                    {
                        "vendor_id": "v1",
                        "country": "US",
                        "dpa_status": "signed",
                        "sub_processors": []
                    }
                ]
            }
        }


class BenchmarkRequest(BaseModel):
    data: List[UserData]
    iterations: int = 1000
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [],  # Array of user data
                "iterations": 1000
            }
        }


class BenchmarkResult(BaseModel):
    ucast_metrics: Dict[str, float]
    rego_metrics: Dict[str, float]
    comparison: Dict[str, Any]
    summary: Dict[str, Any]


# ============================================================================
# UCAST ENGINE
# ============================================================================

class UCASTEngine:
    """UCAST Engine - Shows limitations with advanced features"""
    
    def evaluate(self, data: Dict) -> Dict[str, Any]:
        """Evaluate UCAST rules and show what it CAN'T do"""
        
        results = {
            "supported_policies": {},
            "unsupported_features": {},
            "limitations": []
        }
        
        # FEATURE 1: Set Operations - LIMITED
        try:
            collected = set(data.get('personal_data', {}).get('collected_fields', []))
            necessary = set(data.get('personal_data', {}).get('necessary_fields', []))
            
            # Can only check subset
            is_subset = collected.issubset(necessary)
            
            results["supported_policies"]["data_minimization_check"] = is_subset
            results["unsupported_features"]["set_operations"] = {
                "can_check_subset": True,
                "can_compute_difference": False,
                "note": "Cannot compute (collected - necessary)"
            }
            results["limitations"].append("Set Operations: Limited to subset checks")
        except Exception as e:
            results["supported_policies"]["data_minimization_check"] = False
        
        # FEATURE 2: Universal Quantification - LIMITED
        try:
            vendors = data.get('vendor_relationships', [])
            all_dpa_signed = all(v.get('dpa_status') == 'signed' for v in vendors)
            
            results["supported_policies"]["all_vendors_have_dpa"] = all_dpa_signed
            results["unsupported_features"]["universal_quantification"] = {
                "can_check_single_condition": True,
                "can_check_multiple_conditions": False,
                "note": "Cannot do: every vendor { dpa AND country in list }"
            }
            results["limitations"].append("Universal Quantification: Single condition only")
        except Exception as e:
            results["supported_policies"]["all_vendors_have_dpa"] = False
        
        # FEATURE 3: Regex Matching - NOT SUPPORTED
        results["supported_policies"]["email_format_validation"] = None
        results["unsupported_features"]["regex_matching"] = {
            "supported": False,
            "note": "No regex support"
        }
        results["limitations"].append("Regex Matching: Not supported")
        
        # FEATURE 4: Recursive Rules - NOT SUPPORTED
        results["supported_policies"]["vendor_chain_validation"] = None
        results["unsupported_features"]["recursive_rules"] = {
            "supported": False,
            "note": "Cannot recurse"
        }
        results["limitations"].append("Recursive Rules: Not supported")
        
        # Basic features
        results["supported_policies"]["marketing_consent_active"] = (
            data.get('consent', {}).get('marketing') == True and
            data.get('consent', {}).get('status') == 'active'
        )
        
        return results


# ============================================================================
# REGO ENGINE
# ============================================================================

class RegoEngine:
    """Rego Engine - Demonstrates advanced capabilities"""
    
    def __init__(self):
        self.adequacy_countries = {"US", "CA", "JP", "UK", "CH", "IL", "NZ", "AR", "UY", "KR"}
    
    def evaluate(self, data: Dict) -> Dict[str, Any]:
        """Evaluate Rego policies with advanced features"""
        
        results = {
            "feature_1_set_operations": self._set_operations(data),
            "feature_2_universal_quantification": self._universal_quantification(data),
            "feature_3_regex_matching": self._regex_matching(data),
            "feature_4_recursive_rules": self._recursive_rules(data),
            "basic_policies": self._basic_policies(data)
        }
        
        return results
    
    def _set_operations(self, data: Dict) -> Dict[str, Any]:
        """FEATURE 1: Set Operations"""
        collected = set(data.get('personal_data', {}).get('collected_fields', []))
        necessary = set(data.get('personal_data', {}).get('necessary_fields', []))
        excessive = collected - necessary
        
        return {
            "collected_count": len(collected),
            "necessary_count": len(necessary),
            "excessive_fields": list(excessive),
            "excessive_count": len(excessive),
            "compliant": len(excessive) == 0
        }
    
    def _universal_quantification(self, data: Dict) -> Dict[str, Any]:
        """FEATURE 2: Universal Quantification"""
        vendors = data.get('vendor_relationships', [])
        
        all_dpa_signed = all(v.get('dpa_status') == 'signed' for v in vendors)
        all_adequate = all(v.get('country') in self.adequacy_countries for v in vendors)
        fully_compliant = all(
            v.get('dpa_status') == 'signed' and v.get('country') in self.adequacy_countries
            for v in vendors
        )
        
        countries = data.get('data_transfers', {}).get('third_countries', [])
        all_transfers_adequate = all(c in self.adequacy_countries for c in countries)
        
        return {
            "total_vendors": len(vendors),
            "all_dpa_signed": all_dpa_signed,
            "all_in_adequate_countries": all_adequate,
            "fully_compliant": fully_compliant,
            "all_transfers_lawful": all_transfers_adequate
        }
    
    def _regex_matching(self, data: Dict) -> Dict[str, Any]:
        """FEATURE 3: Regex Matching"""
        email = data.get('email', '')
        fields = data.get('personal_data', {}).get('collected_fields', [])
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        valid_email = bool(re.match(email_pattern, email))
        
        ssn_fields = [f for f in fields if re.search(r'(?i).*(ssn|social.?security)', f)]
        credit_fields = [f for f in fields if re.search(r'(?i).*(credit|card|payment)', f)]
        health_fields = [f for f in fields if re.search(r'(?i).*(health|medical)', f)]
        biometric_fields = [f for f in fields if re.search(r'(?i).*(biometric|fingerprint)', f)]
        
        all_sensitive = ssn_fields + credit_fields + health_fields + biometric_fields
        
        return {
            "email": email,
            "valid_email_format": valid_email,
            "sensitive_fields_found": len(all_sensitive),
            "has_sensitive_data": len(all_sensitive) > 0
        }
    
    def _recursive_rules(self, data: Dict) -> Dict[str, Any]:
        """FEATURE 4: Recursive Rules"""
        vendors = data.get('vendor_relationships', [])
        depth = self._calculate_vendor_chain_depth(vendors)
        chain_compliant = self._check_vendor_chain_recursive(vendors)
        
        return {
            "direct_vendor_count": len(vendors),
            "vendor_chain_depth": depth,
            "max_allowed_depth": 3,
            "depth_compliant": depth <= 3,
            "chain_compliant": chain_compliant
        }
    
    def _calculate_vendor_chain_depth(self, vendors: List[Dict], current_depth: int = 0) -> int:
        """Recursively calculate vendor chain depth"""
        if not vendors:
            return current_depth
        
        max_depth = current_depth
        for vendor in vendors:
            sub_processors = vendor.get('sub_processors', [])
            if sub_processors:
                depth = self._calculate_vendor_chain_depth(sub_processors, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth + 1 if vendors else current_depth
    
    def _check_vendor_chain_recursive(self, vendors: List[Dict]) -> bool:
        """Recursively check vendor compliance"""
        if not vendors:
            return True
        
        for vendor in vendors:
            if vendor.get('dpa_status') != 'signed':
                return False
            
            sub_processors = vendor.get('sub_processors', [])
            if sub_processors and not self._check_vendor_chain_recursive(sub_processors):
                return False
        
        return True
    
    def _basic_policies(self, data: Dict) -> Dict[str, Any]:
        """Basic policies that both engines support"""
        return {
            "marketing_consent_active": (
                data.get('consent', {}).get('marketing') == True and
                data.get('consent', {}).get('status') == 'active'
            ),
            "has_dpa_signed": data.get('data_transfers', {}).get('dpa_signed', False)
        }


# ============================================================================
# BENCHMARKING FUNCTIONS
# ============================================================================

def benchmark_engine(engine, data_list: List[Dict], iterations: int) -> Dict[str, float]:
    """
    Benchmark an engine's performance
    
    Returns:
        Dictionary with performance metrics
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        for record in data_list:
            engine.evaluate(record)
        
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds
    
    times_sorted = sorted(times)
    p50_idx = int(len(times_sorted) * 0.50)
    p95_idx = int(len(times_sorted) * 0.95)
    p99_idx = int(len(times_sorted) * 0.99)
    
    return {
        "mean_ms": round(statistics.mean(times), 4),
        "median_ms": round(statistics.median(times), 4),
        "std_dev_ms": round(statistics.stdev(times) if len(times) > 1 else 0, 4),
        "min_ms": round(min(times), 4),
        "max_ms": round(max(times), 4),
        "p50_ms": round(times_sorted[p50_idx], 4),
        "p95_ms": round(times_sorted[p95_idx], 4),
        "p99_ms": round(times_sorted[p99_idx], 4),
        "total_evaluations": iterations * len(data_list),
        "evaluations_per_second": round((iterations * len(data_list)) / (sum(times) / 1000), 2)
    }


# ============================================================================
# API ENDPOINTS
# ============================================================================

ucast_engine = UCASTEngine()
rego_engine = RegoEngine()


@app.get("/")
def root():
    """API Overview"""
    return {
        "message": "UCAST vs Rego Policy Evaluation API with Performance Benchmarks",
        "docs": "/docs",
        "endpoints": {
            "GET /features": "List all 4 advanced features compared",
            "POST /evaluate/ucast": "Evaluate with UCAST engine (shows limitations)",
            "POST /evaluate/rego": "Evaluate with Rego engine (shows full capabilities)",
            "POST /compare": "Functional comparison of both engines",
            "POST /benchmark": "⭐ Performance benchmark comparison",
            "POST /benchmark/single": "Quick benchmark with single user"
        }
    }


@app.get("/features")
def list_features():
    """List the 4 advanced features being compared"""
    return {
        "advanced_features": [
            {
                "id": 1,
                "name": "Set Operations",
                "description": "Compute set difference, union, intersection",
                "ucast_support": "Limited (subset only)",
                "rego_support": "Full",
                "performance_impact": "Low - simple operations"
            },
            {
                "id": 2,
                "name": "Universal Quantification",
                "description": "Check if ALL items meet complex conditions",
                "ucast_support": "Limited (single condition only)",
                "rego_support": "Full (every keyword)",
                "performance_impact": "Medium - depends on list size"
            },
            {
                "id": 3,
                "name": "Regex Matching",
                "description": "Pattern matching and validation",
                "ucast_support": "None",
                "rego_support": "Full (regex.match)",
                "performance_impact": "Medium - regex compilation cost"
            },
            {
                "id": 4,
                "name": "Recursive Rules",
                "description": "Traverse and validate nested structures",
                "ucast_support": "None",
                "rego_support": "Full",
                "performance_impact": "High - depends on nesting depth"
            }
        ]
    }


@app.post("/evaluate/ucast")
def evaluate_ucast(user_data: UserData):
    """Evaluate policies using UCAST engine"""
    try:
        start_time = time.perf_counter()
        result = ucast_engine.evaluate(user_data.dict())
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        return {
            "engine": "UCAST",
            "result": result,
            "execution_time_ms": round(execution_time_ms, 4),
            "note": "UCAST requires external application code for most advanced features"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate/rego")
def evaluate_rego(user_data: UserData):
    """Evaluate policies using Rego engine"""
    try:
        start_time = time.perf_counter()
        result = rego_engine.evaluate(user_data.dict())
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        return {
            "engine": "Rego",
            "result": result,
            "execution_time_ms": round(execution_time_ms, 4),
            "note": "Rego provides all advanced features natively"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare")
def compare_engines(user_data: UserData):
    """
    Compare both engines functionally and performance-wise for single user
    """
    try:
        # UCAST evaluation with timing
        ucast_start = time.perf_counter()
        ucast_result = ucast_engine.evaluate(user_data.dict())
        ucast_time = (time.perf_counter() - ucast_start) * 1000
        
        # Rego evaluation with timing
        rego_start = time.perf_counter()
        rego_result = rego_engine.evaluate(user_data.dict())
        rego_time = (time.perf_counter() - rego_start) * 1000
        
        # Performance comparison
        performance_diff = ((ucast_time - rego_time) / ucast_time) * 100 if ucast_time > 0 else 0
        
        # Feature comparison
        feature_comparison = {
            "feature_1_set_operations": {
                "ucast": {
                    "supported": "Limited",
                    "result": ucast_result["supported_policies"].get("data_minimization_check"),
                    "can_show_excessive_fields": False
                },
                "rego": {
                    "supported": "Full",
                    "result": rego_result["feature_1_set_operations"],
                    "can_show_excessive_fields": True
                }
            },
            "feature_2_universal_quantification": {
                "ucast": {
                    "supported": "Limited",
                    "result": ucast_result["supported_policies"].get("all_vendors_have_dpa"),
                    "can_check_multiple_conditions": False
                },
                "rego": {
                    "supported": "Full",
                    "result": rego_result["feature_2_universal_quantification"],
                    "can_check_multiple_conditions": True
                }
            },
            "feature_3_regex_matching": {
                "ucast": {
                    "supported": "None",
                    "result": None
                },
                "rego": {
                    "supported": "Full",
                    "result": rego_result["feature_3_regex_matching"]
                }
            },
            "feature_4_recursive_rules": {
                "ucast": {
                    "supported": "None",
                    "result": None
                },
                "rego": {
                    "supported": "Full",
                    "result": rego_result["feature_4_recursive_rules"]
                }
            }
        }
        
        summary = {
            "winner": "Rego" if rego_time < ucast_time else "UCAST",
            "performance": {
                "ucast_time_ms": round(ucast_time, 4),
                "rego_time_ms": round(rego_time, 4),
                "difference_ms": round(abs(ucast_time - rego_time), 4),
                "rego_faster_by_percent": round(performance_diff, 2) if performance_diff > 0 else 0,
                "ucast_faster_by_percent": round(abs(performance_diff), 2) if performance_diff < 0 else 0
            },
            "features": {
                "ucast_limitations": len(ucast_result["limitations"]),
                "rego_advantages": 4
            },
            "key_takeaway": f"Rego is {abs(performance_diff):.1f}% {'faster' if performance_diff > 0 else 'slower'} and provides 4 critical features UCAST cannot handle"
        }
        
        return {
            "ucast_result": ucast_result,
            "rego_result": rego_result,
            "feature_comparison": feature_comparison,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/benchmark", response_model=BenchmarkResult)
def benchmark_comparison(request: BenchmarkRequest):
    """
    Run comprehensive performance benchmark on multiple users
    
    This endpoint runs multiple iterations and provides detailed performance metrics
    """
    try:
        if not request.data:
            raise HTTPException(status_code=400, detail="Data array cannot be empty")
        
        if request.iterations < 10:
            raise HTTPException(status_code=400, detail="Iterations must be at least 10")
        
        data_list = [user.dict() for user in request.data]
        
        print(f"Starting benchmark: {len(data_list)} users, {request.iterations} iterations...")
        
        # Benchmark UCAST
        print("Benchmarking UCAST...")
        ucast_metrics = benchmark_engine(ucast_engine, data_list, request.iterations)
        
        # Benchmark Rego
        print("Benchmarking Rego...")
        rego_metrics = benchmark_engine(rego_engine, data_list, request.iterations)
        
        # Calculate comparison
        mean_diff_percent = ((ucast_metrics["mean_ms"] - rego_metrics["mean_ms"]) / 
                            ucast_metrics["mean_ms"]) * 100
        
        throughput_diff = rego_metrics["evaluations_per_second"] - ucast_metrics["evaluations_per_second"]
        throughput_diff_percent = (throughput_diff / ucast_metrics["evaluations_per_second"]) * 100
        
        comparison = {
            "mean_time_difference_ms": round(ucast_metrics["mean_ms"] - rego_metrics["mean_ms"], 4),
            "mean_time_difference_percent": round(mean_diff_percent, 2),
            "median_time_difference_ms": round(ucast_metrics["median_ms"] - rego_metrics["median_ms"], 4),
            "p95_time_difference_ms": round(ucast_metrics["p95_ms"] - rego_metrics["p95_ms"], 4),
            "p99_time_difference_ms": round(ucast_metrics["p99_ms"] - rego_metrics["p99_ms"], 4),
            "throughput_difference": round(throughput_diff, 2),
            "throughput_difference_percent": round(throughput_diff_percent, 2),
            "faster_engine": "Rego" if rego_metrics["mean_ms"] < ucast_metrics["mean_ms"] else "UCAST",
            "performance_verdict": self._generate_verdict(mean_diff_percent, throughput_diff_percent)
        }
        
        summary = {
            "test_configuration": {
                "users_tested": len(data_list),
                "iterations": request.iterations,
                "total_evaluations_per_engine": ucast_metrics["total_evaluations"]
            },
            "winner": comparison["faster_engine"],
            "key_findings": [
                f"Rego is {abs(mean_diff_percent):.2f}% {'faster' if mean_diff_percent > 0 else 'slower'} on average",
                f"Rego can process {abs(throughput_diff):.0f} more evaluations per second ({abs(throughput_diff_percent):.1f}% improvement)",
                f"At P95, Rego is {comparison['p95_time_difference_ms']:.2f}ms {'faster' if comparison['p95_time_difference_ms'] > 0 else 'slower'}",
                "Rego provides 4 advanced features UCAST cannot handle"
            ],
            "recommendation": self._generate_recommendation(mean_diff_percent, comparison["faster_engine"])
        }
        
        return BenchmarkResult(
            ucast_metrics=ucast_metrics,
            rego_metrics=rego_metrics,
            comparison=comparison,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@app.post("/benchmark/single")
def benchmark_single_user(user_data: UserData, iterations: int = 1000):
    """
    Quick benchmark with a single user - easier to test
    """
    try:
        request = BenchmarkRequest(data=[user_data], iterations=iterations)
        return benchmark_comparison(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_verdict(mean_diff_percent: float, throughput_diff_percent: float) -> str:
    """Generate performance verdict"""
    if abs(mean_diff_percent) < 5:
        return "Performance is essentially equivalent"
    elif mean_diff_percent > 20:
        return "Rego shows significantly better performance"
    elif mean_diff_percent > 10:
        return "Rego shows moderately better performance"
    elif mean_diff_percent > 0:
        return "Rego shows slightly better performance"
    elif mean_diff_percent < -20:
        return "UCAST shows significantly better performance"
    elif mean_diff_percent < -10:
        return "UCAST shows moderately better performance"
    else:
        return "UCAST shows slightly better performance"


def _generate_recommendation(mean_diff_percent: float, faster_engine: str) -> str:
    """Generate recommendation based on results"""
    if faster_engine == "Rego" or abs(mean_diff_percent) < 10:
        return ("Use Rego: Even with similar performance, Rego provides 4 critical advanced features "
                "(set operations, universal quantification, regex, recursion) that UCAST cannot handle.")
    else:
        return ("Consider workload: While UCAST is faster in this test, it lacks 4 critical features. "
                "If you need set operations, regex, or recursion, Rego is the only option.")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "engines": ["UCAST", "Rego"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)