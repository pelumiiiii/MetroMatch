"""Tests for MongoDB cache module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.cache.mongodb_cache import MongoDBCache


class TestMongoDBCache(unittest.TestCase):
    """Test cases for MongoDBCache."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_collection = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client = MagicMock()

        self.mock_client.__getitem__.return_value = self.mock_db
        self.mock_db.bpm_cache = self.mock_collection

    @patch('src.cache.mongodb_cache.MongoClient')
    def test_init(self, mock_mongo_client):
        """Test cache initialization."""
        mock_mongo_client.return_value = self.mock_client

        cache = MongoDBCache("mongodb://localhost:27017")

        mock_mongo_client.assert_called_once_with("mongodb://localhost:27017")
        self.mock_collection.create_index.assert_called()

    @patch('src.cache.mongodb_cache.MongoClient')
    def test_get_hit(self, mock_mongo_client):
        """Test cache hit."""
        mock_mongo_client.return_value = self.mock_client
        self.mock_collection.find_one.return_value = {
            "artist": "test artist",
            "title": "test song",
            "bpm": 120.0
        }

        cache = MongoDBCache("mongodb://localhost:27017")
        result = cache.get("Test Artist", "Test Song")

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for type checker
        self.assertEqual(result["bpm"], 120.0)

    @patch('src.cache.mongodb_cache.MongoClient')
    def test_get_miss(self, mock_mongo_client):
        """Test cache miss."""
        mock_mongo_client.return_value = self.mock_client
        self.mock_collection.find_one.return_value = None

        cache = MongoDBCache("mongodb://localhost:27017")
        result = cache.get("Unknown Artist", "Unknown Song")

        self.assertIsNone(result)

    @patch('src.cache.mongodb_cache.MongoClient')
    def test_set(self, mock_mongo_client):
        """Test setting cache value."""
        mock_mongo_client.return_value = self.mock_client

        cache = MongoDBCache("mongodb://localhost:27017")
        cache.set("Test Artist", "Test Song", 128.5)

        self.mock_collection.update_one.assert_called_once()

    @patch('src.cache.mongodb_cache.MongoClient')
    def test_clear(self, mock_mongo_client):
        """Test clearing cache."""
        mock_mongo_client.return_value = self.mock_client
        self.mock_collection.delete_many.return_value.deleted_count = 10

        cache = MongoDBCache("mongodb://localhost:27017")
        cache.clear()

        self.mock_collection.delete_many.assert_called_once_with({})


if __name__ == '__main__':
    unittest.main()
