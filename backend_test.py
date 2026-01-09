#!/usr/bin/env python3
"""
EUFSI LCA Tool Backend API Testing
Tests all backend endpoints for the Brightway2-powered LCA tool
"""

import requests
import sys
import json
import time
from datetime import datetime

class EUFSILCAAPITester:
    def __init__(self, base_url="https://brightway-tool.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.errors = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.errors.append(f"{name}: {details}")

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data.get('message', 'No message')}"
            self.log_test("API Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Endpoint", False, str(e))
            return False

    def test_industries_endpoint(self):
        """Test industries endpoint"""
        try:
            response = requests.get(f"{self.base_url}/industries", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                # Handle list of industry objects
                if isinstance(data, list):
                    industry_ids = [item.get('id') for item in data if isinstance(item, dict)]
                elif isinstance(data, dict):
                    industries = data.get('industries', {})
                    if isinstance(industries, dict):
                        industry_ids = list(industries.keys())
                    else:
                        industry_ids = [item.get('id') for item in industries if isinstance(item, dict)]
                else:
                    industry_ids = []
                
                expected_industries = ['textile', 'footwear', 'construction', 'battery']
                has_all_industries = all(ind in industry_ids for ind in expected_industries)
                success = has_all_industries
                details += f", Industries found: {industry_ids}"
            self.log_test("Industries Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Industries Endpoint", False, str(e))
            return False

    def test_textile_schema(self):
        """Test textile industry schema endpoint"""
        try:
            response = requests.get(f"{self.base_url}/industries/textile/schema", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                has_sections = 'sections' in data
                success = has_sections and len(data.get('sections', [])) > 0
                details += f", Sections count: {len(data.get('sections', []))}"
            self.log_test("Textile Schema Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Textile Schema Endpoint", False, str(e))
            return False

    def test_lca_databases(self):
        """Test LCA databases endpoint"""
        try:
            response = requests.get(f"{self.base_url}/lca/databases", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                databases = data.get('databases', {})
                expected_dbs = ['USLCI', 'Agribalyse', 'FORWAST']
                has_expected_dbs = any(db in databases for db in expected_dbs)
                success = has_expected_dbs
                details += f", Databases: {list(databases.keys())}"
            self.log_test("LCA Databases Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("LCA Databases Endpoint", False, str(e))
            return False

    def test_lca_methods(self):
        """Test LCA methods endpoint"""
        try:
            response = requests.get(f"{self.base_url}/lca/methods", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                methods = data.get('methods', {})
                expected_methods = ['ReCiPe', 'EF3.1']
                has_expected_methods = any(method in methods for method in expected_methods)
                success = has_expected_methods
                details += f", Methods: {list(methods.keys())}"
            self.log_test("LCA Methods Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("LCA Methods Endpoint", False, str(e))
            return False

    def test_create_project(self):
        """Test creating a new LCA project"""
        try:
            project_data = {
                "name": f"Test Textile Project {datetime.now().strftime('%H%M%S')}",
                "description": "Test project for API testing",
                "industry": "textile",
                "scope": "cradle-to-gate",
                "database": "USLCI",
                "method": "ReCiPe",
                "product_weight_grams": 250,
                "product_scenario": "Casual T-shirt cotton"
            }
            
            response = requests.post(
                f"{self.base_url}/projects", 
                json=project_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            success = response.status_code in [200, 201]  # Accept both 200 and 201
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                self.project_id = data.get('id')
                details += f", Project ID: {self.project_id}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
                    
            self.log_test("Create Project", success, details)
            return success
        except Exception as e:
            self.log_test("Create Project", False, str(e))
            return False

    def test_get_projects(self):
        """Test getting all projects"""
        try:
            response = requests.get(f"{self.base_url}/projects", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                projects_count = len(data) if isinstance(data, list) else 0
                details += f", Projects count: {projects_count}"
            self.log_test("Get Projects", success, details)
            return success
        except Exception as e:
            self.log_test("Get Projects", False, str(e))
            return False

    def test_get_project_by_id(self):
        """Test getting a specific project by ID"""
        if not self.project_id:
            self.log_test("Get Project by ID", False, "No project ID available")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/projects/{self.project_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Project name: {data.get('name', 'N/A')}"
            self.log_test("Get Project by ID", success, details)
            return success
        except Exception as e:
            self.log_test("Get Project by ID", False, str(e))
            return False

    def test_update_project_input_data(self):
        """Test updating project input data"""
        if not self.project_id:
            self.log_test("Update Project Input Data", False, "No project ID available")
            return False
            
        try:
            # Sample textile input data
            input_data = {
                "fibers": [
                    {
                        "material": "Cotton fiber (Global)",
                        "percentage": 100,
                        "production_location": "Global"
                    }
                ],
                "yarns": [
                    {
                        "name": "Cotton yarn",
                        "count_nm": 30,
                        "percentage": 100,
                        "spinning_method": "Ring spinning for weaving, carded yarn"
                    }
                ],
                "fabrics": [
                    {
                        "name": "Cotton fabric",
                        "construction_method": "Weaving - Air jet",
                        "percentage": 100,
                        "finishing_method": "Continuous - natural fibers / fiber blends",
                        "coloring_method": "Jet dyeing - natural fibers / fiber blends",
                        "color_depth": "Medium"
                    }
                ],
                "manufacturing": {
                    "cutting_waste_percentage": 15,
                    "waste_recycled_percentage": 20,
                    "waste_incinerated_percentage": 60,
                    "waste_landfilled_percentage": 20
                },
                "transport": {
                    "final_destination": "Europe",
                    "legs": [
                        {
                            "mode": "Container ship",
                            "distance_km": 8000
                        },
                        {
                            "mode": "Truck",
                            "distance_km": 500
                        }
                    ]
                },
                "use_phase": {
                    "include": False
                },
                "end_of_life": {
                    "include": False
                }
            }
            
            response = requests.put(
                f"{self.base_url}/projects/{self.project_id}/input-data",
                json=input_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            self.log_test("Update Project Input Data", success, details)
            return success
        except Exception as e:
            self.log_test("Update Project Input Data", False, str(e))
            return False

    def test_lca_calculation(self):
        """Test LCA calculation endpoint"""
        if not self.project_id:
            self.log_test("LCA Calculation", False, "No project ID available")
            return False
            
        try:
            response = requests.post(
                f"{self.base_url}/lca/calculate/{self.project_id}",
                timeout=30
            )
            
            success = response.status_code in [200, 202]  # Accept both sync and async responses
            details = f"Status: {response.status_code}"
            
            if success:
                # Wait a bit for calculation to potentially complete
                time.sleep(3)
                
                # Check project status
                status_response = requests.get(f"{self.base_url}/projects/{self.project_id}", timeout=10)
                if status_response.status_code == 200:
                    project_data = status_response.json()
                    project_status = project_data.get('status', 'unknown')
                    details += f", Project status: {project_status}"
                    
                    # If calculation completed, try to get results
                    if project_status == 'completed':
                        results_response = requests.get(f"{self.base_url}/lca/results/{self.project_id}", timeout=10)
                        if results_response.status_code == 200:
                            details += ", Results available"
                        else:
                            details += f", Results status: {results_response.status_code}"
            
            self.log_test("LCA Calculation", success, details)
            return success
        except Exception as e:
            self.log_test("LCA Calculation", False, str(e))
            return False

    def test_get_results(self):
        """Test getting LCA results"""
        if not self.project_id:
            self.log_test("Get LCA Results", False, "No project ID available")
            return False
            
        try:
            # First check if project is completed
            project_response = requests.get(f"{self.base_url}/projects/{self.project_id}", timeout=10)
            if project_response.status_code != 200:
                self.log_test("Get LCA Results", False, "Cannot check project status")
                return False
                
            project_data = project_response.json()
            project_status = project_data.get('status', 'unknown')
            
            if project_status != 'completed':
                self.log_test("Get LCA Results", False, f"Project not completed (status: {project_status})")
                return False
            
            response = requests.get(f"{self.base_url}/lca/results/{self.project_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                impact_categories = data.get('impact_categories', {})
                details += f", Impact categories: {len(impact_categories)}"
                
                # Check for key impact categories
                has_climate_change = 'climate_change' in impact_categories
                details += f", Has climate change: {has_climate_change}"
                
            self.log_test("Get LCA Results", success, details)
            return success
        except Exception as e:
            self.log_test("Get LCA Results", False, str(e))
            return False

    def test_pdf_report(self):
        """Test PDF report generation"""
        if not self.project_id:
            self.log_test("PDF Report Generation", False, "No project ID available")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/reports/{self.project_id}/pdf",
                timeout=30
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                content_type = response.headers.get('content-type', '')
                is_pdf = 'pdf' in content_type.lower()
                content_length = len(response.content)
                details += f", Content-Type: {content_type}, Size: {content_length} bytes"
                success = is_pdf and content_length > 1000  # Basic PDF validation
                
            self.log_test("PDF Report Generation", success, details)
            return success
        except Exception as e:
            self.log_test("PDF Report Generation", False, str(e))
            return False

    def test_lca_stages_endpoint(self):
        """Test LCA stages endpoint for textile industry"""
        try:
            response = requests.get(f"{self.base_url}/lca/stages/textile", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                stages = data.get('stages', [])
                details += f", Stages count: {len(stages)}"
                
                # Check for expected textile stages
                expected_stages = ['raw_materials', 'yarn_production', 'fabric_production', 'dyeing_finishing']
                stage_ids = [stage.get('id') for stage in stages if isinstance(stage, dict)]
                has_expected_stages = any(stage in stage_ids for stage in expected_stages)
                success = has_expected_stages and len(stages) > 0
                details += f", Stage IDs: {stage_ids}"
                
            self.log_test("LCA Stages Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("LCA Stages Endpoint", False, str(e))
            return False

    def test_impact_categories_endpoint(self):
        """Test impact categories endpoint"""
        try:
            response = requests.get(f"{self.base_url}/lca/impact-categories/ReCiPe", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                categories = data.get('categories', {})
                details += f", Categories count: {len(categories)}"
                
                # Check for key impact categories
                expected_categories = ['climate_change', 'water_depletion', 'terrestrial_acidification']
                has_expected_categories = any(cat in categories for cat in expected_categories)
                success = has_expected_categories and len(categories) > 0
                details += f", Has expected categories: {has_expected_categories}"
                
            self.log_test("Impact Categories Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Impact Categories Endpoint", False, str(e))
            return False

    def test_impact_trace_endpoint(self):
        """Test impact trace endpoint with test project"""
        # Use the provided test project ID
        test_project_id = "b3122015-0732-42ca-bd6a-eaa940e5fbfd"
        
        try:
            # Test with climate_change and yarn_production as specified in requirements
            response = requests.get(
                f"{self.base_url}/lca/trace/{test_project_id}?impact_category=climate_change&life_cycle_stage=yarn_production",
                timeout=15
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                
                # Check required fields in response
                required_fields = ['impact_category', 'life_cycle_stage', 'activities', 'total_stage_impact', 'methodology']
                has_required_fields = all(field in data for field in required_fields)
                
                activities = data.get('activities', [])
                methodology = data.get('methodology', {})
                
                details += f", Activities count: {len(activities)}"
                details += f", Has methodology: {'formula' in methodology}"
                details += f", Total impact: {data.get('total_stage_impact', 'N/A')}"
                
                # Check if activities have exchanges with characterization factors
                has_exchanges = False
                if activities:
                    for activity in activities:
                        exchanges = activity.get('exchanges', [])
                        if exchanges:
                            has_exchanges = True
                            # Check if exchanges have required fields
                            first_exchange = exchanges[0]
                            exchange_fields = ['flow_name', 'emission_amount', 'characterization_factor', 'impact_contribution']
                            has_exchange_fields = all(field in first_exchange for field in exchange_fields)
                            details += f", Exchange fields complete: {has_exchange_fields}"
                            break
                
                success = has_required_fields and (len(activities) > 0 or data.get('total_stage_impact', 0) >= 0)
                details += f", Has exchanges: {has_exchanges}"
                
            self.log_test("Impact Trace Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Impact Trace Endpoint", False, str(e))
            return False

    def test_impact_trace_with_current_project(self):
        """Test impact trace endpoint with current test project"""
        if not self.project_id:
            self.log_test("Impact Trace (Current Project)", False, "No project ID available")
            return False
            
        try:
            # First ensure project has completed calculation
            project_response = requests.get(f"{self.base_url}/projects/{self.project_id}", timeout=10)
            if project_response.status_code != 200:
                self.log_test("Impact Trace (Current Project)", False, "Cannot check project status")
                return False
                
            project_data = project_response.json()
            project_status = project_data.get('status', 'unknown')
            
            if project_status != 'completed':
                self.log_test("Impact Trace (Current Project)", False, f"Project not completed (status: {project_status})")
                return False
            
            # Test with textile stages
            response = requests.get(
                f"{self.base_url}/lca/trace/{self.project_id}?impact_category=climate_change&life_cycle_stage=yarn_production",
                timeout=15
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                activities = data.get('activities', [])
                total_impact = data.get('total_stage_impact', 0)
                details += f", Activities: {len(activities)}, Total impact: {total_impact}"
                
            self.log_test("Impact Trace (Current Project)", success, details)
            return success
        except Exception as e:
            self.log_test("Impact Trace (Current Project)", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🧪 Starting EUFSI LCA Tool Backend API Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Basic endpoint tests
        self.test_api_root()
        self.test_industries_endpoint()
        self.test_textile_schema()
        self.test_lca_databases()
        self.test_lca_methods()
        
        # Project CRUD tests
        self.test_create_project()
        self.test_get_projects()
        self.test_get_project_by_id()
        self.test_update_project_input_data()
        
        # LCA calculation tests
        self.test_lca_calculation()
        
        # Wait a bit more for calculation to complete
        if self.project_id:
            print("⏳ Waiting for calculation to complete...")
            time.sleep(5)
            
            # Check status multiple times
            for i in range(3):
                try:
                    status_response = requests.get(f"{self.base_url}/projects/{self.project_id}", timeout=10)
                    if status_response.status_code == 200:
                        project_data = status_response.json()
                        status = project_data.get('status', 'unknown')
                        print(f"   Status check {i+1}: {status}")
                        if status == 'completed':
                            break
                        elif status == 'error':
                            print("   ❌ Calculation failed")
                            break
                    time.sleep(3)
                except:
                    pass
        
        self.test_get_results()
        self.test_pdf_report()
        
        # Test new Impact Traceability endpoints
        self.test_lca_stages_endpoint()
        self.test_impact_categories_endpoint()
        self.test_impact_trace_endpoint()
        self.test_impact_trace_with_current_project()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.errors:
            print("\n❌ Failed Tests:")
            for error in self.errors:
                print(f"   • {error}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = EUFSILCAAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())