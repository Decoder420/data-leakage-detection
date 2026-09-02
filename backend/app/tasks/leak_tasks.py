"""Async Celery tasks for large dataset leak processing — DecodeX Security Technologies."""

from backend.app.tasks.celery_app import celery_app
from backend.app.engine.guilt_calculator import compute_vectorized_guilt_probabilities
from typing import List, Dict, Set, Any


@celery_app.task(bind=True, name="tasks.process_large_leak_analysis")
def process_large_leak_analysis_task(
    self,
    leaked_record_hashes: List[str],
    agent_record_map: Dict[str, List[str]],  # serialized as list of hashes
    canary_ownership_map: Dict[str, str],
    independent_leak_prob_p: float = 0.05
):
    """
    Asynchronous Celery task for processing large leak dumps (100k+ rows).
    """
    self.update_state(state="PROGRESS", meta={"progress": 0.2, "status": "Indexing distributed records"})
    
    agent_set_map = {a_id: set(r_hashes) for a_id, r_hashes in agent_record_map.items()}
    
    self.update_state(state="PROGRESS", meta={"progress": 0.5, "status": "Vectorized guilt calculation in progress"})
    
    results = compute_vectorized_guilt_probabilities(
        leaked_record_hashes=leaked_record_hashes,
        agent_record_map=agent_set_map,
        canary_ownership_map=canary_ownership_map,
        independent_leak_prob_p=independent_leak_prob_p
    )
    
    self.update_state(state="PROGRESS", meta={"progress": 1.0, "status": "Analysis completed"})
    return results
