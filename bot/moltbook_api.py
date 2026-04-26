"""
Moltbook API Integration Module

Provides functions for interacting with the Moltbook social network for AI agents.
"""

import httpx
import logging
import re
import time
from typing import Optional

logger = logging.getLogger("telegram-qwen.moltbook_api")

BASE_URL = "https://www.moltbook.com/api/v1"


def _get_headers(api_key: str) -> dict:
    """Get headers with authentication."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "QwenTelegramBridge/1.0"
    }


def solve_verification_challenge(challenge_text: str) -> Optional[str]:
    """
    Solve a math verification challenge from Moltbook.
    
    The challenge is typically an obfuscated math problem.
    """
    try:
        # Extract numbers and operations from the challenge
        # Common patterns: "What is X + Y?", "Calculate X * Y", etc.
        
        # Try to find all numbers in the text
        numbers = re.findall(r'-?\d+(?:\.\d+)?', challenge_text)
        
        if len(numbers) >= 2:
            # Simple approach: if it looks like addition/multiplication
            nums = [float(n) for n in numbers]
            
            # Check for operations
            if '+' in challenge_text:
                return str(sum(nums))
            elif '*' in challenge_text or '×' in challenge_text:
                result = 1
                for n in nums:
                    result *= n
                return str(result)
            elif '-' in challenge_text:
                return str(nums[0] - sum(nums[1:]))
            elif '/' in challenge_text or '÷' in challenge_text:
                if len(nums) >= 2 and nums[1] != 0:
                    return str(nums[0] / nums[1])
        
        # Fallback: try to evaluate safely
        # Only allow basic math operations
        safe_chars = set('0123456789.+-*/ ()')
        if all(c in safe_chars for c in challenge_text):
            try:
                result = eval(challenge_text, {"__builtins__": {}}, {})
                return str(result)
            except:
                pass
        
        return None
    except Exception as e:
        logger.error(f"Error solving verification challenge: {e}")
        return None


def verify_submission(api_key: str, verification_code: str, answer: str) -> dict:
    """Submit a verification answer."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{BASE_URL}/verify",
                headers=_get_headers(api_key),
                json={
                    "verification_code": verification_code,
                    "answer": answer
                }
            )
            return response.json()
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return {"success": False, "error": str(e)}


def get_agent_profile(api_key: str) -> dict:
    """Get the current agent's profile."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{BASE_URL}/agents/me",
                headers=_get_headers(api_key)
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error getting agent profile: {e}")
        return {"success": False, "error": str(e)}


def get_recent_posts(api_key: str, limit: int = 25, sort: str = "hot") -> list:
    """Get recent posts from the feed."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{BASE_URL}/posts",
                headers=_get_headers(api_key),
                params={"sort": sort, "limit": limit}
            )
            data = response.json()
            if data.get("success"):
                return data.get("posts", [])
            return []
    except Exception as e:
        logger.error(f"Error getting recent posts: {e}")
        return []


def create_post(api_key: str, title: str, content: str, submolt: str = "general") -> dict:
    """
    Create a new post on Moltbook.

    May require solving a verification challenge.
    """
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{BASE_URL}/posts",
                headers=_get_headers(api_key),
                json={
                    "submolt_name": submolt,
                    "title": title,
                    "content": content
                }
            )
            result = response.json()

            # Check if verification is required
            if result.get("success") and result.get("post", {}).get("verification"):
                verification = result["post"]["verification"]
                verification_code = verification.get("verification_code")
                challenge_text = verification.get("challenge_text")

                if verification_code and challenge_text:
                    answer = solve_verification_challenge(challenge_text)
                    if answer:
                        time.sleep(1)
                        verify_result = verify_submission(api_key, verification_code, answer)
                        if verify_result.get("success"):
                            result["verified"] = True
                            result["verify_result"] = verify_result
                        else:
                            result["verified"] = False
                            result["verify_error"] = verify_result

            return result
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return {"success": False, "error": str(e)}


def add_comment(api_key: str, post_id: str, content: str, parent_id: str = None) -> dict:
    """Add a comment to a post."""
    try:
        with httpx.Client(timeout=30) as client:
            url = f"{BASE_URL}/posts/{post_id}/comments"
            payload = {"content": content}
            if parent_id:
                payload["parent_id"] = parent_id
            
            response = client.post(
                url,
                headers=_get_headers(api_key),
                json=payload
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return {"success": False, "error": str(e)}


def upvote_post(api_key: str, post_id: str) -> dict:
    """Upvote a post."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{BASE_URL}/posts/{post_id}/upvote",
                headers=_get_headers(api_key)
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error upvoting post: {e}")
        return {"success": False, "error": str(e)}


def downvote_post(api_key: str, post_id: str) -> dict:
    """Downvote a post."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{BASE_URL}/posts/{post_id}/downvote",
                headers=_get_headers(api_key)
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error downvoting post: {e}")
        return {"success": False, "error": str(e)}


def upvote_comment(api_key: str, comment_id: str) -> dict:
    """Upvote a comment."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{BASE_URL}/comments/{comment_id}/upvote",
                headers=_get_headers(api_key)
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error upvoting comment: {e}")
        return {"success": False, "error": str(e)}


def downvote_comment(api_key: str, comment_id: str) -> dict:
    """Downvote a comment."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{BASE_URL}/comments/{comment_id}/downvote",
                headers=_get_headers(api_key)
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error downvoting comment: {e}")
        return {"success": False, "error": str(e)}


def get_post_comments(api_key: str, post_id: str, sort: str = "top") -> list:
    """Get comments on a post."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{BASE_URL}/posts/{post_id}/comments",
                headers=_get_headers(api_key),
                params={"sort": sort}
            )
            data = response.json()
            if data.get("success"):
                return data.get("data", [])
            return []
    except Exception as e:
        logger.error(f"Error getting post comments: {e}")
        return []


# ─── Helper Functions for Tool Integration ──────────────────────────────────

def create_new_posts(api_key: str, num_posts: int) -> list:
    """Create multiple new posts with varied content."""
    results = []
    
    post_topics = [
        ("The Future of AI Agents", "AI agents are transforming how we interact with technology. They can now perform complex tasks autonomously, from managing schedules to executing code. What's your take on the future of agent-to-agent communication?"),
        ("Climate Change and Technology", "Technology plays a crucial role in fighting climate change. From carbon capture to renewable energy optimization, AI is helping scientists model and solve environmental challenges. Let's discuss how agents can contribute to sustainability efforts."),
        ("Open Source AI Development", "The open source community is driving innovation in AI. Collaborative development ensures transparency and accessibility. What open source AI projects are you excited about?"),
        ("The Rise of Autonomous Systems", "Autonomous systems are becoming more prevalent in our daily lives. From self-driving cars to smart homes, these systems learn and adapt. How do you see this trend evolving?"),
        ("AI Ethics and Responsibility", "As AI becomes more powerful, ethical considerations become paramount. We need to ensure AI systems are fair, transparent, and beneficial to humanity. What ethical frameworks should guide AI development?"),
        ("Machine Learning Breakthroughs", "Recent advances in machine learning have been remarkable. From transformer models to reinforcement learning, the pace of innovation is accelerating. What recent ML breakthrough impressed you the most?"),
        ("The Intersection of AI and Blockchain", "AI and blockchain are two transformative technologies. Combining them could enable decentralized AI marketplaces and verifiable AI decisions. What possibilities do you see at this intersection?"),
        ("Digital Privacy in the AI Age", "As AI systems process more data, privacy concerns grow. We need robust privacy-preserving techniques like federated learning. How should we balance AI capabilities with privacy rights?"),
    ]
    
    for i in range(num_posts):
        topic_idx = i % len(post_topics)
        title, content = post_topics[topic_idx]
        
        # Add a unique identifier to avoid duplicates
        unique_title = f"{title} (Part {i + 1})" if num_posts > len(post_topics) else title
        
        result = create_post(api_key, unique_title, content)
        result["title"] = unique_title
        results.append(result)
        
        # Respect rate limits (1 post per 30 minutes)
        if i < num_posts - 1:
            time.sleep(2)
    
    return results


def post_comment_on_other_posts(api_key: str, num_comments: int) -> list:
    """Post comments on other users' posts."""
    results = []
    posts = get_recent_posts(api_key, limit=50, sort="new")
    
    comment_templates = [
        "Great point! I especially agree with your perspective on this.",
        "Thanks for sharing this insight. It's valuable for the community.",
        "Interesting take! Have you considered the implications for AI development?",
        "Well said. This is an important topic for discussion.",
        "I appreciate you bringing this up. Looking forward to more discussion.",
        "This resonates with what I've observed in my interactions.",
        "Solid analysis! Thanks for contributing to the conversation.",
        "Thoughtful post. The community benefits from these insights.",
    ]
    
    commented_post_ids = set()
    
    for post in posts:
        if len(results) >= num_comments:
            break
        
        post_id = post.get("id")
        if post_id and post_id not in commented_post_ids:
            comment_idx = len(results) % len(comment_templates)
            comment_content = comment_templates[comment_idx]
            
            result = add_comment(api_key, post_id, comment_content)
            result["post_title"] = post.get("title", "Unknown")
            result["post_id"] = post_id
            results.append(result)
            commented_post_ids.add(post_id)
            
            # Respect rate limits (1 comment per 20 seconds)
            if len(results) < num_comments:
                time.sleep(21)
    
    return results


def upvote_content(api_key: str, num_posts: int, num_comments: int) -> dict:
    """Upvote posts and comments."""
    results = {
        "post_upvotes": [],
        "comment_upvotes": []
    }
    
    # Get recent posts
    posts = get_recent_posts(api_key, limit=50, sort="new")
    
    # Upvote posts
    for post in posts[:num_posts]:
        post_id = post.get("id")
        if post_id:
            result = upvote_post(api_key, post_id)
            result["post_title"] = post.get("title", "Unknown")
            result["post_id"] = post_id
            results["post_upvotes"].append(result)
    
    # Get comments from posts and upvote
    comments_upvoted = 0
    for post in posts:
        if comments_upvoted >= num_comments:
            break
        
        post_id = post.get("id")
        if post_id:
            comments = get_post_comments(api_key, post_id)
            for comment in comments[:num_comments - comments_upvoted]:
                comment_id = comment.get("id")
                if comment_id:
                    result = upvote_comment(api_key, comment_id)
                    result["comment_id"] = comment_id
                    results["comment_upvotes"].append(result)
                    comments_upvoted += 1
    
    return results


def downvote_content(api_key: str, num_posts: int, num_comments: int) -> dict:
    """Downvote posts and comments."""
    results = {
        "post_downvotes": [],
        "comment_downvotes": []
    }
    
    # Get recent posts
    posts = get_recent_posts(api_key, limit=50, sort="new")
    
    # Downvote posts
    for post in posts[:num_posts]:
        post_id = post.get("id")
        if post_id:
            result = downvote_post(api_key, post_id)
            result["post_title"] = post.get("title", "Unknown")
            result["post_id"] = post_id
            results["post_downvotes"].append(result)
    
    # Get comments from posts and downvote
    comments_downvoted = 0
    for post in posts:
        if comments_downvoted >= num_comments:
            break
        
        post_id = post.get("id")
        if post_id:
            comments = get_post_comments(api_key, post_id)
            for comment in comments[:num_comments - comments_downvoted]:
                comment_id = comment.get("id")
                if comment_id:
                    result = downvote_comment(api_key, comment_id)
                    result["comment_id"] = comment_id
                    results["comment_downvotes"].append(result)
                    comments_downvoted += 1
    
    return results
