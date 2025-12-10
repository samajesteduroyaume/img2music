"""
Load testing script for img2music application.
Tests performance under concurrent load.
"""
import requests
import time
import concurrent.futures
from PIL import Image
import io
import base64
import json


def create_test_image(color='red', size=(100, 100)):
    """Create a simple test image."""
    img = Image.new('RGB', size, color=color)
    return img


def image_to_base64(img):
    """Convert PIL image to base64 string."""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def test_single_request(url, image_data, test_id):
    """Test a single request to the API."""
    start_time = time.time()
    
    try:
        # Simulate Gradio API call
        response = requests.post(
            f"{url}/api/predict",
            json={
                "data": [image_data, None, "piano", False, False, True]
            },
            timeout=60
        )
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            return {
                'test_id': test_id,
                'success': True,
                'duration': duration,
                'status_code': response.status_code
            }
        else:
            return {
                'test_id': test_id,
                'success': False,
                'duration': duration,
                'status_code': response.status_code,
                'error': response.text
            }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'test_id': test_id,
            'success': False,
            'duration': duration,
            'error': str(e)
        }


def run_load_test(url="http://localhost:7860", num_requests=10, concurrent_workers=3):
    """
    Run load test on the application.
    
    Args:
        url: Base URL of the application
        num_requests: Total number of requests to make
        concurrent_workers: Number of concurrent workers
    """
    print(f"🧪 Starting load test...")
    print(f"   URL: {url}")
    print(f"   Requests: {num_requests}")
    print(f"   Concurrent workers: {concurrent_workers}")
    print()
    
    # Create test images
    test_images = [
        create_test_image('red'),
        create_test_image('blue'),
        create_test_image('green'),
    ]
    
    # Convert to base64
    image_data_list = [image_to_base64(img) for img in test_images]
    
    # Prepare test cases
    test_cases = []
    for i in range(num_requests):
        test_cases.append({
            'url': url,
            'image_data': image_data_list[i % len(image_data_list)],
            'test_id': i
        })
    
    # Run tests concurrently
    start_time = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [
            executor.submit(test_single_request, tc['url'], tc['image_data'], tc['test_id'])
            for tc in test_cases
        ]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            
            status = "✅" if result['success'] else "❌"
            print(f"{status} Test {result['test_id']}: {result['duration']:.2f}s")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        durations = [r['duration'] for r in successful]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
    else:
        avg_duration = min_duration = max_duration = 0
    
    # Print summary
    print()
    print("=" * 60)
    print("📊 LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Total requests: {num_requests}")
    print(f"Successful: {len(successful)} ({len(successful)/num_requests*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/num_requests*100:.1f}%)")
    print(f"Total time: {total_time:.2f}s")
    print(f"Requests/second: {num_requests/total_time:.2f}")
    print()
    print(f"Response times (successful requests):")
    print(f"  Average: {avg_duration:.2f}s")
    print(f"  Min: {min_duration:.2f}s")
    print(f"  Max: {max_duration:.2f}s")
    print("=" * 60)
    
    # Show errors if any
    if failed:
        print()
        print("❌ ERRORS:")
        for r in failed[:5]:  # Show first 5 errors
            print(f"  Test {r['test_id']}: {r.get('error', 'Unknown error')}")
    
    return {
        'total_requests': num_requests,
        'successful': len(successful),
        'failed': len(failed),
        'total_time': total_time,
        'avg_duration': avg_duration,
        'min_duration': min_duration,
        'max_duration': max_duration,
        'requests_per_second': num_requests / total_time
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load test for img2music')
    parser.add_argument('--url', default='http://localhost:7860', help='Base URL')
    parser.add_argument('--requests', type=int, default=10, help='Number of requests')
    parser.add_argument('--workers', type=int, default=3, help='Concurrent workers')
    
    args = parser.parse_args()
    
    results = run_load_test(
        url=args.url,
        num_requests=args.requests,
        concurrent_workers=args.workers
    )
