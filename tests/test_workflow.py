# # tests/test_workflow.py - Test for the LinkedIn workflow
# import pytest
# from unittest.mock import patch, MagicMock
# from your_package_name.main import create_workflow
# from your_package_name.state import WorkflowState, NewsArticle, LinkedInArticle, ValidationResult

# @pytest.fixture
# def sample_news_articles():
#     """Sample news articles for testing."""
#     return [
#         NewsArticle(
#             title="AI Breakthrough in Healthcare",
#             url="https://example.com/news/1",
#             summary="New AI model helps doctors diagnose rare diseases faster.",
#             published_date="2025-03-01T12:00:00Z",
#             source="Tech Health News"
#         ),
#         NewsArticle(
#             title="Healthcare Providers Adopt AI Tools",
#             url="https://example.com/news/2",
#             summary="Major hospitals implement AI-powered diagnostic systems.",
#             published_date="2025-03-02T10:30:00Z",
#             source="Healthcare Daily"
#         )
#     ]

# @pytest.fixture
# def sample_linkedin_article():
#     """Sample LinkedIn article for testing."""
#     return LinkedInArticle(
#         title="Revolutionizing Healthcare: How AI is Changing the Medical Landscape",
#         content="The healthcare industry is witnessing a paradigm shift...",
#         hashtags=["#AIinHealthcare", "#MedTech", "#Innovation", "#HealthTech", "#FutureMedicine"],
#         call_to_action="What are your thoughts on AI's role in healthcare? Share your experiences below!",
#         target_audience="Healthcare professionals, technologists, and innovation leaders"
#     )

# @pytest.fixture
# def sample_validation_result():
#     """Sample validation result for testing."""
#     return ValidationResult(
#         is_valid=True,
#         issues=[],
#         suggestions=["Consider adding a personal anecdote", "Add more statistical data"]
#     )

# def test_workflow_creation():
#     """Test that the workflow graph can be created."""
#     workflow = create_workflow()
#     assert workflow is not None

# @patch('your_package_name.agents.news_fetcher')
# def test_news_fetcher_step(mock_news_fetcher, sample_news_articles):
#     """Test the news fetcher step."""
#     # Setup the mock
#     state = WorkflowState(
#         messages=[{"role": "user", "content": "Create a LinkedIn article about AI in Healthcare"}],
#         current_step="news_fetcher"
#     )
    
#     expected_state = state.model_copy(deep=True)
#     expected_state.news_articles = sample_news_articles
#     expected_state.current_step = "linkedin_article_writer"
#     expected_state.messages.append({"role": "assistant", "content": "Fetched 2 relevant news articles."})
    
#     mock_news_fetcher.return_value = expected_state
    
#     # Create and run the workflow with just the first step
#     workflow = create_workflow()
#     result = workflow.invoke(state, {"config": {"rss_feed_url": "https://example.com/rss"}})
    
#     # Verify the result
#     assert mock_news_fetcher.called
#     assert result.current_step == "linkedin_article_writer"
#     assert len(result.news_articles) == 2

# # tests/test_tools.py - Test for tools
# import pytest
# from unittest.mock import patch, MagicMock
# from your_package_name.tools import fetch_rss_feed
# import feedparser

# @patch('your_package_name.tools.feedparser.parse')
# def test_fetch_rss_feed(mock_parse):
#     """Test the RSS feed fetching tool."""
#     # Setup mock
#     mock_feed = MagicMock()
#     mock_feed.feed.title = "Tech News"
    
#     mock_entry1 = MagicMock()
#     mock_entry1.title = "AI in Healthcare"
#     mock_entry1.link = "https://example.com/1"
#     mock_entry1.summary = "A breakthrough in healthcare"
#     mock_entry1.published = "2025-03-01T12:00:00Z"
    
#     mock_entry2 = MagicMock()
#     mock_entry2.title = "New AI Models"
#     mock_entry2.link = "https://example.com/2"
#     mock_entry2.summary = "Revolutionary AI models"
#     mock_entry2.published = "2025-03-02T12:00:00Z"
    
#     mock_feed.entries = [mock_entry1, mock_entry2]
#     mock_parse.return_value = mock_feed
    
#     # Call the function
#     result = fetch_rss_feed("https://example.com/rss", limit=2)
    
#     # Verify results
#     assert len(result) == 2
#     assert result[0]["title"] == "AI in Healthcare"
#     assert result[1]["title"] == "New AI Models"
#     assert "error" not in result[0]
#     assert "error" not in result[1]

# @patch('your_package_name.tools.feedparser.parse')
# def test_fetch_rss_feed_error(mock_parse):
#     """Test error handling in the RSS feed fetching tool."""
#     # Setup mock to raise an exception
#     mock_parse.side_effect = Exception("Failed to parse feed")
    
#     # Call the function
#     result = fetch_rss_feed("https://example.com/bad-rss")
    
#     # Verify error handling
#     assert len(result) == 1
#     assert "error" in result[0]
#     assert "Failed to fetch RSS feed" in result[0]["error"]
