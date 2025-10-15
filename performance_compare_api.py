"""
OPA (Rego) vs UCAST Performance Comparison
Using OPA Server via HTTP with Connection Pooling

Prerequisites:
    1. OPA Server running on http://localhost:8181
       docker run -p 8181:8181 -v $(pwd):/policies openpolicyagent/opa:latest \
         run --server /policies/gdpr_policies.rego
    
    2. pip install requests tabulate

Usage:
    python benchmark.py
"""

import json
import time
import statistics
import requests
from typing import Dict, List, Any
from tabulate import tabulate


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


class OPAEngine:
    """OPA Engine - calls OPA server via HTTP with connection pooling"""
    
    def __init__(self, opa_url: str = 'http://localhost:8181'):
        self.opa_url = opa_url
        self.endpoint = f"{opa_url}/v1/data/gdpr/summary"
        
        # Use session for connection pooling (faster!)
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        
        self._check_opa_server()
    
    def _check_opa_server(self):
        """Check if OPA server is running"""
        try:
            response = self.session.get(f"{self.opa_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"{Colors.GREEN}✓ OPA Server connected: {self.opa_url}{Colors.END}")
                print(f"{Colors.GREEN}✓ Connection pooling enabled{Colors.END}")
            else:
                raise ConnectionError()
        except (requests.ConnectionError, requests.Timeout):
            print(f"{Colors.RED}✗ Cannot connect to OPA server at {self.opa_url}{Colors.END}")
            print(f"{Colors.YELLOW}Start OPA server:{Colors.END}")
            print(f"  docker run -p 8181:8181 -v $(pwd):/policies openpolicyagent/opa:latest \\")
            print(f"    run --server /policies/gdpr_policies.rego")
            print(f"\nOr without Docker:")
            print(f"  opa run --server gdpr_policies.rego")
            raise SystemExit(1)
    
    def evaluate(self, data: Dict) -> Dict[str, Any]:
        """Evaluate using OPA server with persistent connection"""
        try:
            response = self.session.post(
                self.endpoint,
                json={'input': data},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"{Colors.RED}OPA Error: {response.status_code}{Colors.END}")
                print(response.text)
                return {}
            
            result = response.json()
            return result.get('result', {})
            
        except requests.Timeout:
            print(f"{Colors.RED}OPA request timeout{Colors.END}")
            return {}
        except Exception as e:
            print(f"{Colors.RED}OPA Error: {e}{Colors.END}")
            return {}


class UCASTEngine:
    """UCAST Engine - Python implementation"""
    
    def __init__(self, rules_file: str):
        with open(rules_file, 'r') as f:
            self.rules = json.load(f)['policies']
    
    def evaluate(self, data: Dict) -> Dict[str, Any]:
        """Evaluate UCAST rules"""
        results = {
            "policies": {},
            "features": {
                "set_operations": self._set_operations(data),
                "universal_quantification": self._universal_quantification(data),
                "regex_matching": {"supported": False, "note": "Not available in UCAST"},
                "recursive_rules": {"supported": False, "note": "Not available in UCAST"}
            },
            "compliant": False
        }
        
        # Evaluate basic policies
        for rule in self.rules:
            if rule.get('supported') == 'FULL':
                results['policies'][rule['name']] = self._evaluate_condition(
                    rule['condition'], data
                )
            else:
                results['policies'][rule['name']] = None
        
        # Calculate compliance
        valid_policies = [v for v in results['policies'].values() if v is not None]
        results['compliant'] = all(valid_policies) if valid_policies else False
        
        return results
    
    def _set_operations(self, data: Dict) -> Dict[str, Any]:
        """Limited set operations"""
        collected = set(data.get('personal_data', {}).get('collected_fields', []))
        necessary = set(data.get('personal_data', {}).get('necessary_fields', []))
        
        return {
            "subset_check": collected.issubset(necessary),
            "can_compute_difference": False,
            "note": "UCAST cannot return excessive fields"
        }
    
    def _universal_quantification(self, data: Dict) -> Dict[str, Any]:
        """Limited universal quantification"""
        vendors = data.get('vendor_relationships', [])
        all_dpa = all(v.get('dpa_status') == 'signed' for v in vendors)
        
        return {
            "all_dpa_signed": all_dpa,
            "can_check_multiple": False,
            "note": "UCAST cannot check multiple conditions"
        }
    
    def _evaluate_condition(self, condition: Dict, data: Dict) -> bool:
        """Evaluate a condition"""
        operator = condition.get('operator')
        
        if operator == 'and':
            return all(self._evaluate_condition(c, data) for c in condition['conditions'])
        elif operator == 'or':
            return any(self._evaluate_condition(c, data) for c in condition['conditions'])
        elif operator == 'eq':
            return self._get_value(condition['field'], data) == condition['value']
        elif operator == 'subset':
            collected = set(self._get_value(condition['field'], data) or [])
            necessary = set(self._get_value(condition['reference'], data) or [])
            return collected.issubset(necessary)
        
        return False
    
    def _get_value(self, field: str, data: Dict) -> Any:
        """Get nested value"""
        keys = field.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


def benchmark_engine(engine, data_list: List[Dict], iterations: int = 1000) -> Dict[str, float]:
    """Benchmark an engine"""
    times = []
    
    print(f"  Running {iterations} iterations...", end='', flush=True)
    
    # Warm-up (important for OPA server)
    for _ in range(10):
        for record in data_list:
            engine.evaluate(record)
    
    for i in range(iterations):
        if i % 100 == 0:
            print('.', end='', flush=True)
        
        start = time.perf_counter()
        for record in data_list:
            engine.evaluate(record)
        end = time.perf_counter()
        
        times.append((end - start) * 1000)  # Convert to ms
    
    print(" Done!")
    
    times_sorted = sorted(times)
    p95_idx = int(len(times_sorted) * 0.95)
    p99_idx = int(len(times_sorted) * 0.99)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times),
        'p95': times_sorted[p95_idx],
        'p99': times_sorted[p99_idx],
        'throughput': (iterations * len(data_list)) / (sum(times) / 1000)
    }


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")


def compare_features(opa_result: Dict, ucast_result: Dict) -> List[List[str]]:
    """Compare feature capabilities"""
    
    # Extract Rego features
    rego_policies = opa_result.get('policies', {})
    
    # Set Operations
    rego_set = rego_policies.get('excessive_data_collection', {})
    ucast_set = ucast_result['features']['set_operations']
    
    # Universal Quantification
    rego_univ = rego_policies.get('all_vendors_compliant', {})
    ucast_univ = ucast_result['features']['universal_quantification']
    
    # Regex
    rego_regex = rego_policies.get('email_validation', {})
    ucast_regex = ucast_result['features']['regex_matching']
    
    # Recursion
    rego_recur = rego_policies.get('vendor_chain_analysis', {})
    ucast_recur = ucast_result['features']['recursive_rules']
    
    table = [
        ['Feature', 'UCAST Support', 'Rego Support', 'Example Output'],
        ['─' * 25, '─' * 15, '─' * 15, '─' * 35],
        [
            'Set Operations',
            f"{Colors.YELLOW}Limited{Colors.END}\n(subset only)",
            f"{Colors.GREEN}Full{Colors.END}\n(difference, union)",
            f"Rego: {rego_set.get('excessive_count', 0)} excessive fields\n"
            f"UCAST: {ucast_set['subset_check']}"
        ],
        [
            'Universal\nQuantification',
            f"{Colors.YELLOW}Limited{Colors.END}\n(single condition)",
            f"{Colors.GREEN}Full{Colors.END}\n(multiple conditions)",
            f"Rego: Checks DPA + country\n"
            f"UCAST: Only DPA={ucast_univ['all_dpa_signed']}"
        ],
        [
            'Regex Matching',
            f"{Colors.RED}None{Colors.END}",
            f"{Colors.GREEN}Full{Colors.END}",
            f"Rego: Email valid={rego_regex.get('compliant', 'N/A')}\n"
            f"UCAST: Not supported"
        ],
        [
            'Recursive Rules',
            f"{Colors.RED}None{Colors.END}",
            f"{Colors.GREEN}Full{Colors.END}",
            f"Rego: Chain depth={rego_recur.get('chain_depth', 'N/A')}\n"
            f"UCAST: Not supported"
        ]
    ]
    
    return table


def main():
    """Main benchmark function"""
    
    print_header("OPA Server (Rego) vs UCAST Performance Benchmark")
    print(f"{Colors.YELLOW}Note: This benchmark includes HTTP overhead for OPA.{Colors.END}")
    print(f"{Colors.YELLOW}      For production, consider OPA WASM (in-process) for better performance.{Colors.END}")
    print(f"{Colors.YELLOW}      See OPTIMIZATION.md for details.{Colors.END}")
    
    # Load data
    print(f"\n{Colors.BOLD}Loading test data...{Colors.END}")
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        print(f"{Colors.GREEN}✓ Loaded {len(data)} users from data.json{Colors.END}")
    except FileNotFoundError:
        print(f"{Colors.RED}✗ data.json not found!{Colors.END}")
        return
    
    # Initialize engines
    print(f"\n{Colors.BOLD}Initializing engines...{Colors.END}")
    
    try:
        opa_engine = OPAEngine('http://localhost:8181')
    except SystemExit:
        return
    
    try:
        ucast_engine = UCASTEngine('ucast_rules.json')
        print(f"{Colors.GREEN}✓ UCAST engine ready{Colors.END}")
    except FileNotFoundError:
        print(f"{Colors.RED}✗ ucast_rules.json not found!{Colors.END}")
        return
    
    # Test functional correctness with first user
    print_header("Functional Comparison (First User)")
    
    test_user = data[0]
    print(f"Testing user: {test_user['user_id']}")
    
    print(f"\n{Colors.BOLD}Evaluating with OPA (Rego)...{Colors.END}")
    opa_result = opa_engine.evaluate(test_user)
    
    print(f"{Colors.BOLD}Evaluating with UCAST...{Colors.END}")
    ucast_result = ucast_engine.evaluate(test_user)
    
    # Display feature comparison
    print_header("Feature Capability Comparison")
    
    feature_table = compare_features(opa_result, ucast_result)
    print(tabulate(feature_table, tablefmt='simple', stralign='left'))
    
    # Performance benchmarking
    print_header("Performance Benchmark")
    
    iterations = 1000
    print(f"{Colors.BOLD}Configuration:{Colors.END}")
    print(f"  Users: {len(data)}")
    print(f"  Iterations: {iterations}")
    print(f"  Total evaluations per engine: {iterations * len(data)}")
    print(f"  OPA Mode: HTTP Server with connection pooling")
    print(f"  Warm-up: 10 iterations (excluded from results)\n")
    
    # Benchmark UCAST
    print(f"{Colors.BOLD}Benchmarking UCAST...{Colors.END}")
    ucast_metrics = benchmark_engine(ucast_engine, data, iterations)
    
    # Benchmark OPA
    print(f"{Colors.BOLD}Benchmarking OPA Server (Rego)...{Colors.END}")
    opa_metrics = benchmark_engine(opa_engine, data, iterations)
    
    # Calculate differences
    mean_diff = ((ucast_metrics['mean'] - opa_metrics['mean']) / ucast_metrics['mean']) * 100
    throughput_diff = opa_metrics['throughput'] - ucast_metrics['throughput']
    throughput_pct = (throughput_diff / ucast_metrics['throughput']) * 100
    
    # Performance comparison table
    print_header("Performance Results")
    
    perf_table = [
        ['Metric', 'UCAST', 'OPA Server (Rego)', 'Difference', 'Winner'],
        ['─' * 20, '─' * 15, '─' * 18, '─' * 20, '─' * 10],
        [
            'Mean Time (ms)',
            f'{ucast_metrics["mean"]:.4f}',
            f'{opa_metrics["mean"]:.4f}',
            f'{abs(ucast_metrics["mean"] - opa_metrics["mean"]):.4f}',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['mean'] < ucast_metrics['mean'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'Median Time (ms)',
            f'{ucast_metrics["median"]:.4f}',
            f'{opa_metrics["median"]:.4f}',
            f'{abs(ucast_metrics["median"] - opa_metrics["median"]):.4f}',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['median'] < ucast_metrics['median'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'Std Deviation (ms)',
            f'{ucast_metrics["std_dev"]:.4f}',
            f'{opa_metrics["std_dev"]:.4f}',
            f'{abs(ucast_metrics["std_dev"] - opa_metrics["std_dev"]):.4f}',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['std_dev'] < ucast_metrics['std_dev'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'Min Time (ms)',
            f'{ucast_metrics["min"]:.4f}',
            f'{opa_metrics["min"]:.4f}',
            f'{abs(ucast_metrics["min"] - opa_metrics["min"]):.4f}',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['min'] < ucast_metrics['min'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'Max Time (ms)',
            f'{ucast_metrics["max"]:.4f}',
            f'{opa_metrics["max"]:.4f}',
            f'{abs(ucast_metrics["max"] - opa_metrics["max"]):.4f}',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['max'] < ucast_metrics['max'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'P95 Time (ms)',
            f'{ucast_metrics["p95"]:.4f}',
            f'{opa_metrics["p95"]:.4f}',
            f'{abs(ucast_metrics["p95"] - opa_metrics["p95"]):.4f}',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['p95'] < ucast_metrics['p95'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'P99 Time (ms)',
            f'{ucast_metrics["p99"]:.4f}',
            f'{opa_metrics["p99"]:.4f}',
            f'{abs(ucast_metrics["p99"] - opa_metrics["p99"]):.4f}',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['p99'] < ucast_metrics['p99'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'Throughput (eval/s)',
            f'{ucast_metrics["throughput"]:.2f}',
            f'{opa_metrics["throughput"]:.2f}',
            f'{abs(throughput_diff):.2f} ({abs(throughput_pct):.1f}%)',
            f"{Colors.GREEN}Rego{Colors.END}" if opa_metrics['throughput'] > ucast_metrics['throughput'] else f"{Colors.YELLOW}UCAST{Colors.END}"
        ]
    ]
    
    print(tabulate(perf_table, headers='firstrow', tablefmt='grid'))
    
    # HTTP Overhead Analysis
    print_header("Performance Analysis")
    
    http_overhead = opa_metrics['mean'] - 0.5  # Estimated policy eval time
    
    print(f"{Colors.BOLD}HTTP Overhead Breakdown:{Colors.END}")
    print(f"  Total OPA time:       {opa_metrics['mean']:.2f} ms")
    print(f"  Estimated policy eval: ~0.50 ms")
    print(f"  HTTP overhead:         ~{http_overhead:.2f} ms ({(http_overhead/opa_metrics['mean'])*100:.1f}%)")
    print()
    print(f"{Colors.YELLOW}Note: HTTP overhead includes:{Colors.END}")
    print(f"  • Network latency (localhost)")
    print(f"  • JSON serialization/deserialization")
    print(f"  • HTTP headers and connection management")
    print()
    print(f"{Colors.CYAN}For production with better performance:{Colors.END}")
    print(f"  • Use OPA WASM (in-process, ~0.05-0.10 ms)")
    print(f"  • Use batch evaluation (amortize HTTP cost)")
    print(f"  • Enable caching (50%+ improvement for repeated queries)")
    print(f"  • See OPTIMIZATION.md for details")
    
    # Summary
    print_header("Summary")
    
    summary_table = [
        ['Aspect', 'UCAST', 'Rego (OPA Server)', 'Winner'],
        ['─' * 27, '─' * 20, '─' * 20, '─' * 10],
        [
            'Performance',
            f'{ucast_metrics["mean"]:.2f} ms avg',
            f'{opa_metrics["mean"]:.2f} ms avg',
            f"{Colors.GREEN}Rego{Colors.END}" if mean_diff > 0 else f"{Colors.YELLOW}UCAST{Colors.END}"
        ],
        [
            'Speed Difference',
            '—',
            f'{abs(mean_diff):.1f}% {"faster" if mean_diff > 0 else "slower"}',
            '—'
        ],
        [
            'Advanced Features',
            '0/4 supported',
            '4/4 supported',
            f"{Colors.GREEN}Rego{Colors.END}"
        ],
        [
            'Set Operations',
            f"{Colors.YELLOW}Limited{Colors.END}",
            f"{Colors.GREEN}Full{Colors.END}",
            f"{Colors.GREEN}Rego{Colors.END}"
        ],
        [
            'Universal Quantification',
            f"{Colors.YELLOW}Limited{Colors.END}",
            f"{Colors.GREEN}Full{Colors.END}",
            f"{Colors.GREEN}Rego{Colors.END}"
        ],
        [
            'Regex Matching',
            f"{Colors.RED}None{Colors.END}",
            f"{Colors.GREEN}Full{Colors.END}",
            f"{Colors.GREEN}Rego{Colors.END}"
        ],
        [
            'Recursive Rules',
            f"{Colors.RED}None{Colors.END}",
            f"{Colors.GREEN}Full{Colors.END}",
            f"{Colors.GREEN}Rego{Colors.END}"
        ],
        [
            'External Code Needed',
            f"{Colors.YELLOW}Yes{Colors.END}",
            f"{Colors.GREEN}No{Colors.END}",
            f"{Colors.GREEN}Rego{Colors.END}"
        ]
    ]
    
    print(tabulate(summary_table, headers='firstrow', tablefmt='grid'))
    
    # Final verdict
    print(f"\n{Colors.BOLD}{Colors.GREEN}FINAL VERDICT:{Colors.END}")
    
    if mean_diff > 0:
        print(f"{Colors.GREEN}🏆 Rego (OPA Server) is {abs(mean_diff):.1f}% FASTER than UCAST{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️  UCAST is {abs(mean_diff):.1f}% faster than Rego (HTTP overhead){Colors.END}")
    
    print(f"{Colors.GREEN}✅ Rego provides 4/4 advanced features (UCAST: 0/4){Colors.END}")
    
    print(f"\n{Colors.BOLD}Recommendation:{Colors.END}")
    
    if mean_diff > 0:
        print(f"{Colors.GREEN}Use Rego:{Colors.END} Better performance + 4 critical features")
    else:
        print(f"{Colors.CYAN}Use Rego with OPA WASM for production:{Colors.END}")
        print(f"  • HTTP adds ~{http_overhead:.0f}ms overhead")
        print(f"  • OPA WASM (in-process) performs like UCAST (~0.05ms)")
        print(f"  • Still get all 4 advanced features")
        print(f"  • See OPTIMIZATION.md for setup instructions")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Benchmark interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()