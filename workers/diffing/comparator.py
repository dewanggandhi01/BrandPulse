from __future__ import annotations
import difflib
from typing import Any, Dict, List, Tuple

class SnapshotComparator:
    """
    Computes structural similarity ratios and granular diff chunks between two snapshot text block lists.
    """

    @classmethod
    def compare(cls, old_blocks: List[str], new_blocks: List[str]) -> Dict[str, Any]:
        """
        Compares two lists of text blocks and produces similarity metrics and structured diff operations.
        """
        old_text = "\n".join(old_blocks)
        new_text = "\n".join(new_blocks)

        # 1. Similarity Ratio via SequenceMatcher
        matcher = difflib.SequenceMatcher(None, old_blocks, new_blocks)
        similarity_ratio = round(matcher.ratio(), 4)

        # 2. Structured Diff Chunks
        diff_chunks: List[Dict[str, Any]] = []
        additions = 0
        deletions = 0
        modifications = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for block in old_blocks[i1:i2]:
                    diff_chunks.append({
                        'type': 'unchanged',
                        'content': block
                    })
            elif tag == 'insert':
                for block in new_blocks[j1:j2]:
                    additions += 1
                    diff_chunks.append({
                        'type': 'added',
                        'content': block
                    })
            elif tag == 'delete':
                for block in old_blocks[i1:i2]:
                    deletions += 1
                    diff_chunks.append({
                        'type': 'removed',
                        'content': block
                    })
            elif tag == 'replace':
                old_slice = old_blocks[i1:i2]
                new_slice = new_blocks[j1:j2]
                modifications += max(len(old_slice), len(new_slice))
                diff_chunks.append({
                    'type': 'modified',
                    'old_content': "\n".join(old_slice),
                    'new_content': "\n".join(new_slice)
                })

        # 3. Standard Unified Diff String
        unified = list(difflib.unified_diff(
            old_blocks,
            new_blocks,
            fromfile='previous_snapshot',
            tofile='current_snapshot',
            lineterm=''
        ))

        # 4. Word count calculation
        old_word_count = len(old_text.split())
        new_word_count = len(new_text.split())
        word_delta = new_word_count - old_word_count

        return {
            'similarity_ratio': similarity_ratio,
            'is_identical': similarity_ratio == 1.0,
            'additions_count': additions,
            'deletions_count': deletions,
            'modifications_count': modifications,
            'total_changes': additions + deletions + modifications,
            'old_word_count': old_word_count,
            'new_word_count': new_word_count,
            'word_delta': word_delta,
            'diff_chunks': diff_chunks,
            'unified_diff': "\n".join(unified[:200])  # limit to top 200 lines
        }
