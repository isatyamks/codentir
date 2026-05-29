import pymongo
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
from src.config import settings

class DBManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            try:
                cls._instance.client = pymongo.MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
                cls._instance.db = cls._instance.client[settings.MONGO_DB_NAME]
                
                # Collections
                cls._instance.projects = cls._instance.db["projects"]
                cls._instance.documents = cls._instance.db["documents"]
                cls._instance.requirements = cls._instance.db["requirements"]
                cls._instance.use_cases = cls._instance.db["use_cases"]
                cls._instance.test_cases = cls._instance.db["test_cases"]
                cls._instance.clarifications = cls._instance.db["clarifications"]
                cls._instance.chunks = cls._instance.db["chunks"]
                
                # Indexes for performance
                cls._instance.documents.create_index("project_id")
                cls._instance.requirements.create_index("project_id")
                cls._instance.use_cases.create_index("project_id")
                cls._instance.test_cases.create_index("project_id")
                cls._instance.clarifications.create_index("project_id")
                cls._instance.chunks.create_index("document_id")
            except Exception as e:
                print(f"Error connecting to MongoDB: {e}")
                cls._instance.db = None
                
        return cls._instance

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    # --- Projects ---
    def create_project(self, name: str, domain: str, description: str) -> str:
        project_id = str(uuid.uuid4())
        doc = {
            "_id": project_id,
            "name": name,
            "domain": domain,
            "description": description,
            "status": "Active",
            "coverage_score": 0,
            "created_at": self._now()
        }
        self.projects.insert_one(doc)
        return project_id

    def get_projects(self) -> List[Dict]:
        return list(self.projects.find())
        
    def get_project(self, project_id: str) -> Optional[Dict]:
        return self.projects.find_one({"_id": project_id})
        
    def update_project_coverage(self, project_id: str, score: int):
        self.projects.update_one({"_id": project_id}, {"$set": {"coverage_score": score}})

    # --- Documents ---
    def add_document(self, project_id: str, filename: str, file_path: str):
        doc_id = str(uuid.uuid4())
        self.documents.insert_one({
            "_id": doc_id,
            "project_id": project_id,
            "filename": filename,
            "file_path": file_path,
            "status": "Indexed",
            "created_at": self._now()
        })
        return doc_id

    def save_processed_document(self, metadata: Dict, chunks: List[Dict]) -> str:
        doc_id = str(uuid.uuid4())
        
        # Save metadata
        document_doc = {
            "_id": doc_id,
            "filename": metadata.get("file_name", "unknown"),
            "metadata": metadata,
            "created_at": self._now()
        }
        self.documents.insert_one(document_doc)
        
        # Save chunks
        if chunks:
            chunk_docs = []
            for chunk in chunks:
                chunk_doc = chunk.copy()
                chunk_doc["document_id"] = doc_id
                chunk_doc["created_at"] = self._now()
                chunk_docs.append(chunk_doc)
                
            self.chunks.insert_many(chunk_docs)
            
        return doc_id

    # --- Requirements ---
    def add_requirement(self, project_id: str, text: str, source: str) -> str:
        req_id = str(uuid.uuid4())
        self.requirements.insert_one({
            "_id": req_id,
            "project_id": project_id,
            "text": text,
            "type": "Functional",
            "priority": "High",
            "status": "Analyzed",
            "coverage": "Full",
            "source_document": source,
            "confidence": 95,
            "dependencies": [],
            "created_at": self._now()
        })
        return req_id
        
    def get_requirements(self, project_id: str = None) -> List[Dict]:
        query = {"project_id": project_id} if project_id else {}
        return list(self.requirements.find(query))

    # --- Use Cases ---
    def add_use_case(self, project_id: str, requirement_id: str, data: Dict) -> str:
        uc_id = str(uuid.uuid4())
        self.use_cases.insert_one({
            "_id": uc_id,
            "project_id": project_id,
            "requirement_id": requirement_id,
            "title": data.get("title", "Untitled Use Case"),
            "description": data.get("description", ""),
            "preconditions": data.get("preconditions", []),
            "steps": data.get("steps", []),
            "expected_result": data.get("expected_result", ""),
            "negative_cases": data.get("negative_cases", []),
            "boundary_cases": data.get("boundary_cases", []),
            "created_at": self._now()
        })
        return uc_id
        
    def get_use_cases(self, requirement_id: str = None) -> List[Dict]:
        query = {"requirement_id": requirement_id} if requirement_id else {}
        return list(self.use_cases.find(query))

    # --- Test Cases ---
    def add_test_case(self, project_id: str, use_case_id: str, data: Dict) -> str:
        tc_id = str(uuid.uuid4())
        
        # Simple heuristic for automation logic based on title/type
        title_lower = data.get("title", "").lower()
        framework = "Selenium" if "login" in title_lower or "concurrent" in title_lower else "Playwright"
        complexity = "High" if "negative" in data.get("type", "").lower() else "Medium"

        self.test_cases.insert_one({
            "_id": tc_id,
            "project_id": project_id,
            "use_case_id": use_case_id,
            "title": data.get("title", "Untitled Test"),
            "type": data.get("type", "Positive"),
            "priority": data.get("priority", "Medium"),
            "category": data.get("category", "Functional"),
            "status": "Automated",
            "test_data": data.get("test_data", {}),
            "steps": data.get("steps", []),
            "expected_result": data.get("expected_result", ""),
            "target_framework": framework,
            "complexity": complexity,
            "created_at": self._now()
        })
        return tc_id
        
    def get_test_cases(self, use_case_id: str = None) -> List[Dict]:
        query = {"use_case_id": use_case_id} if use_case_id else {}
        return list(self.test_cases.find(query))
        
    def get_all_test_cases_for_project(self, project_id: str = None) -> List[Dict]:
        query = {"project_id": project_id} if project_id else {}
        return list(self.test_cases.find(query))

    # --- Clarifications ---
    def add_clarification(self, project_id: str, title: str, context: str, impact: str) -> str:
        clar_id = str(uuid.uuid4())
        self.clarifications.insert_one({
            "_id": clar_id,
            "project_id": project_id,
            "title": title,
            "context": context,
            "impact": impact,
            "status": "Open",
            "created_at": self._now()
        })
        return clar_id

    def get_clarifications(self, project_id: str = None) -> List[Dict]:
        query = {"project_id": project_id} if project_id else {}
        return list(self.clarifications.find(query))
