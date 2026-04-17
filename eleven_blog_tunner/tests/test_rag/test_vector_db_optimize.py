import pytest
from unittest.mock import patch, MagicMock
from eleven_blog_tunner.rag.vector_db_optimize import VectorDBOptimizer


class TestVectorDBOptimizer:
    """VectorDBOptimizer 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.optimizer = VectorDBOptimizer()

    def test_initialization(self):
        """测试初始化"""
        assert self.optimizer.vector_db_path is not None
        assert self.optimizer.collection_name == "documents"

    @patch('chromadb.PersistentClient')
    def test_optimize(self, mock_client):
        """测试优化功能"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_collection = MagicMock()
        mock_instance.get_collection.return_value = mock_collection

        result = self.optimizer.optimize()

        assert result["success"] is True

    @patch('chromadb.PersistentClient')
    def test_create_collection(self, mock_client):
        """测试创建集合"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        result = self.optimizer.create_collection("test_collection")

        assert "test_collection" in result
        mock_instance.create_collection.assert_called_once_with("test_collection")

    @patch('chromadb.PersistentClient')
    def test_list_collections(self, mock_client):
        """测试列出集合"""
        mock_instance = MagicMock()
        mock_instance.list_collections.return_value = ["collection1", "collection2"]
        mock_client.return_value = mock_instance

        result = self.optimizer.list_collections()

        assert len(result) == 2
        assert "collection1" in result
        assert "collection2" in result

    @patch('chromadb.PersistentClient')
    def test_get_statistics(self, mock_client):
        """测试获取统计信息"""
        mock_instance = MagicMock()
        mock_instance.list_collections.return_value = ["documents"]
        mock_instance.get_collection.return_value = MagicMock()
        mock_client.return_value = mock_instance

        stats = self.optimizer.get_statistics()

        assert isinstance(stats, dict)
        assert "documents" in stats

    @patch('shutil.copy2')
    @patch('shutil.copytree')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.mkdir')
    def test_backup(self, mock_mkdir, mock_iterdir, mock_copytree, mock_copy2):
        """测试备份功能"""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        self.optimizer.vector_db_path = mock_path

        mock_iterdir.return_value = [MagicMock(is_file=lambda: True)]

        result = self.optimizer.backup("./backup")

        assert result["success"] is True

    @patch('shutil.rmtree')
    @patch('shutil.copy2')
    @patch('shutil.copytree')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_restore(self, mock_exists, mock_mkdir, mock_iterdir, mock_copytree, mock_copy2, mock_rmtree):
        """测试恢复功能"""
        mock_exists.return_value = False

        mock_path = MagicMock()
        self.optimizer.vector_db_path = mock_path

        mock_iterdir.return_value = [MagicMock(is_file=lambda: True)]

        result = self.optimizer.restore("./backup")

        assert result["success"] is True

    @patch('chromadb.PersistentClient')
    def test_cleanup_old_data(self, mock_client):
        """测试清理旧数据"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        self.optimizer._cleanup_old_data()

        mock_instance.get_collection.assert_not_called()

    @patch('chromadb.PersistentClient')
    def test_optimize_index(self, mock_client):
        """测试索引优化"""
        mock_instance = MagicMock()
        mock_collection = MagicMock()
        mock_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_instance

        self.optimizer._optimize_index()

        mock_instance.get_collection.assert_called()

    @patch('chromadb.PersistentClient')
    def test_compact_data(self, mock_client):
        """测试数据压缩"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        self.optimizer._compact_data()
