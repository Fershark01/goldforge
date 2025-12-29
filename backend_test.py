#!/usr/bin/env python3
"""
GOALFORGE 2026 Backend API Testing Suite
Tests all authentication, categories, and goals endpoints
"""

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class GoalForgeAPITester:
    def __init__(self, base_url="https://goals-twenty-six.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.test_user_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        self.test_user_password = "TestPass123!"
        self.test_user_name = "Test User"
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Store created resources for cleanup
        self.created_categories = []
        self.created_goals = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            return success, response_data, response.status_code

        except Exception as e:
            return False, {"error": str(e)}, 0

    # ============ AUTHENTICATION TESTS ============

    def test_user_registration(self):
        """Test user registration endpoint"""
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "name": self.test_user_name
        }
        
        success, response_data, status_code = self.make_request('POST', 'auth/register', data, 200)
        
        if success and 'token' in response_data and 'user' in response_data:
            self.token = response_data['token']
            self.user_id = response_data['user']['id']
            self.log_test("User Registration", True, f"User ID: {self.user_id}", response_data)
            return True
        else:
            self.log_test("User Registration", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_user_login(self):
        """Test user login endpoint"""
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, response_data, status_code = self.make_request('POST', 'auth/login', data, 200)
        
        if success and 'token' in response_data:
            # Update token for subsequent tests
            self.token = response_data['token']
            self.log_test("User Login", True, "Login successful", response_data)
            return True
        else:
            self.log_test("User Login", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_get_user_profile(self):
        """Test get current user profile"""
        success, response_data, status_code = self.make_request('GET', 'auth/me', expected_status=200)
        
        if success and 'id' in response_data and 'email' in response_data:
            self.log_test("Get User Profile", True, f"User: {response_data.get('name')}", response_data)
            return True
        else:
            self.log_test("Get User Profile", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        success, response_data, status_code = self.make_request('POST', 'auth/login', data, 401)
        
        if success:
            self.log_test("Invalid Login (Expected 401)", True, "Correctly rejected invalid credentials")
            return True
        else:
            self.log_test("Invalid Login (Expected 401)", False, f"Status: {status_code}, should be 401")
            return False

    # ============ CATEGORY TESTS ============

    def test_get_default_categories(self):
        """Test that default categories are created on registration"""
        success, response_data, status_code = self.make_request('GET', 'categories', expected_status=200)
        
        if success and isinstance(response_data, list):
            expected_categories = ["Health", "Professional", "Spiritual", "Hobbies"]
            found_categories = [cat['name'] for cat in response_data]
            
            all_found = all(cat in found_categories for cat in expected_categories)
            
            if all_found and len(response_data) == 4:
                self.log_test("Default Categories Created", True, f"Found: {found_categories}", response_data)
                return True
            else:
                self.log_test("Default Categories Created", False, f"Expected {expected_categories}, got {found_categories}")
                return False
        else:
            self.log_test("Default Categories Created", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_create_category(self):
        """Test creating a new category"""
        data = {
            "name": "Test Category",
            "icon": "🧪",
            "image_url": "https://example.com/test.jpg"
        }
        
        success, response_data, status_code = self.make_request('POST', 'categories', data, 200)
        
        if success and 'id' in response_data:
            self.created_categories.append(response_data['id'])
            self.log_test("Create Category", True, f"Category ID: {response_data['id']}", response_data)
            return response_data['id']
        else:
            self.log_test("Create Category", False, f"Status: {status_code}, Response: {response_data}")
            return None

    def test_update_category(self, category_id):
        """Test updating a category"""
        if not category_id:
            self.log_test("Update Category", False, "No category ID provided")
            return False
            
        data = {
            "name": "Updated Test Category",
            "icon": "🔬"
        }
        
        success, response_data, status_code = self.make_request('PUT', f'categories/{category_id}', data, 200)
        
        if success and response_data.get('name') == "Updated Test Category":
            self.log_test("Update Category", True, "Category updated successfully", response_data)
            return True
        else:
            self.log_test("Update Category", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_delete_category(self, category_id):
        """Test deleting a category"""
        if not category_id:
            self.log_test("Delete Category", False, "No category ID provided")
            return False
            
        success, response_data, status_code = self.make_request('DELETE', f'categories/{category_id}', expected_status=200)
        
        if success:
            self.log_test("Delete Category", True, "Category deleted successfully", response_data)
            if category_id in self.created_categories:
                self.created_categories.remove(category_id)
            return True
        else:
            self.log_test("Delete Category", False, f"Status: {status_code}, Response: {response_data}")
            return False

    # ============ GOAL TESTS ============

    def test_create_goal(self, category_id):
        """Test creating a new goal"""
        if not category_id:
            self.log_test("Create Goal", False, "No category ID provided")
            return None
            
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        data = {
            "category_id": category_id,
            "text": "Test Goal - Learn new technology",
            "priority": "high",
            "deadline": future_date
        }
        
        success, response_data, status_code = self.make_request('POST', 'goals', data, 200)
        
        if success and 'id' in response_data:
            self.created_goals.append(response_data['id'])
            self.log_test("Create Goal", True, f"Goal ID: {response_data['id']}", response_data)
            return response_data['id']
        else:
            self.log_test("Create Goal", False, f"Status: {status_code}, Response: {response_data}")
            return None

    def test_get_goals_by_category(self, category_id):
        """Test getting goals filtered by category"""
        if not category_id:
            self.log_test("Get Goals by Category", False, "No category ID provided")
            return False
            
        success, response_data, status_code = self.make_request('GET', f'goals?category_id={category_id}', expected_status=200)
        
        if success and isinstance(response_data, list):
            self.log_test("Get Goals by Category", True, f"Found {len(response_data)} goals", response_data)
            return True
        else:
            self.log_test("Get Goals by Category", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_toggle_goal_completion(self, goal_id):
        """Test toggling goal completion status"""
        if not goal_id:
            self.log_test("Toggle Goal Completion", False, "No goal ID provided")
            return False
            
        success, response_data, status_code = self.make_request('PATCH', f'goals/{goal_id}/toggle', expected_status=200)
        
        if success and 'completed' in response_data:
            completion_status = response_data['completed']
            self.log_test("Toggle Goal Completion", True, f"Goal completed: {completion_status}", response_data)
            return True
        else:
            self.log_test("Toggle Goal Completion", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_update_goal(self, goal_id):
        """Test updating a goal"""
        if not goal_id:
            self.log_test("Update Goal", False, "No goal ID provided")
            return False
            
        data = {
            "text": "Updated Test Goal - Master new technology",
            "priority": "medium"
        }
        
        success, response_data, status_code = self.make_request('PUT', f'goals/{goal_id}', data, 200)
        
        if success and response_data.get('text') == data['text']:
            self.log_test("Update Goal", True, "Goal updated successfully", response_data)
            return True
        else:
            self.log_test("Update Goal", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_delete_goal(self, goal_id):
        """Test deleting a goal"""
        if not goal_id:
            self.log_test("Delete Goal", False, "No goal ID provided")
            return False
            
        success, response_data, status_code = self.make_request('DELETE', f'goals/{goal_id}', expected_status=200)
        
        if success:
            self.log_test("Delete Goal", True, "Goal deleted successfully", response_data)
            if goal_id in self.created_goals:
                self.created_goals.remove(goal_id)
            return True
        else:
            self.log_test("Delete Goal", False, f"Status: {status_code}, Response: {response_data}")
            return False

    def test_categories_with_progress(self):
        """Test that categories return progress information"""
        success, response_data, status_code = self.make_request('GET', 'categories', expected_status=200)
        
        if success and isinstance(response_data, list) and len(response_data) > 0:
            first_category = response_data[0]
            required_fields = ['total_goals', 'completed_goals', 'progress']
            
            has_progress_fields = all(field in first_category for field in required_fields)
            
            if has_progress_fields:
                self.log_test("Categories with Progress", True, f"Progress fields present: {required_fields}")
                return True
            else:
                missing_fields = [field for field in required_fields if field not in first_category]
                self.log_test("Categories with Progress", False, f"Missing fields: {missing_fields}")
                return False
        else:
            self.log_test("Categories with Progress", False, f"Status: {status_code}, Response: {response_data}")
            return False

    # ============ MAIN TEST RUNNER ============

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting GOALFORGE 2026 Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        # Test API root endpoint
        success, response_data, status_code = self.make_request('GET', '', expected_status=200)
        self.log_test("API Root Endpoint", success, f"Status: {status_code}")

        # Authentication Tests
        print("\n🔐 AUTHENTICATION TESTS")
        if not self.test_user_registration():
            print("❌ Registration failed - stopping tests")
            return self.generate_report()

        self.test_user_login()
        self.test_get_user_profile()
        self.test_invalid_login()

        # Category Tests
        print("\n📁 CATEGORY TESTS")
        self.test_get_default_categories()
        
        # Create a test category for goal tests
        test_category_id = self.test_create_category()
        if test_category_id:
            self.test_update_category(test_category_id)
            
        self.test_categories_with_progress()

        # Goal Tests
        print("\n🎯 GOAL TESTS")
        if test_category_id:
            test_goal_id = self.test_create_goal(test_category_id)
            self.test_get_goals_by_category(test_category_id)
            
            if test_goal_id:
                self.test_toggle_goal_completion(test_goal_id)
                self.test_update_goal(test_goal_id)
                self.test_delete_goal(test_goal_id)
            
            # Clean up test category
            self.test_delete_category(test_category_id)

        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['name']}: {result['details']}")
        
        # Return exit code
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    """Main test execution"""
    tester = GoalForgeAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())