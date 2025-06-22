"""
Module for chunking text for LLM processing.
"""
import logging

# Configure logging
logger = logging.getLogger(__name__)

def chunk_text(text, chunk_size=1000, overlap=100, respect_paragraphs=True):
    """
    Split text into chunks for processing by LLM with improved handling of text boundaries.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Maximum size of each chunk
        overlap (int): Overlap between chunks in characters
        respect_paragraphs (bool): Try to keep paragraphs together when possible
        
    Returns:
        list: List of dictionaries containing:
            - 'content': The text chunk
            - 'index': Chunk index
            - 'start_char': Starting character position in original text
            - 'end_char': Ending character position in original text
    """
    if not text:
        return []
    
    logger.info(f"Chunking text of {len(text)} characters (chunk_size={chunk_size}, overlap={overlap})")
    chunks = []
    
    # If respecting paragraphs, split by paragraph first
    if respect_paragraphs:
        # Split text by paragraph breaks (double newlines)
        paragraphs = text.split('\n\n')
        # Filter out empty paragraphs and track their positions in original text
        filtered_paragraphs = []
        current_pos = 0
        for para in paragraphs:
            para_stripped = para.strip()
            if para_stripped:
                # Find the actual start position of this paragraph in the original text
                para_start = text.find(para_stripped, current_pos)
                filtered_paragraphs.append((para_stripped, para_start))
                current_pos = para_start + len(para_stripped)
        
        current_buffer = ""
        buffer_start_pos = 0
        
        for para_text, para_original_pos in filtered_paragraphs:
            # If this paragraph is too long for a single chunk, handle it specially
            if len(para_text) > chunk_size:
                # First, finalize any existing buffer
                if current_buffer:
                    chunks.append({
                        'content': current_buffer,
                        'index': len(chunks),
                        'start_char': buffer_start_pos,
                        'end_char': buffer_start_pos + len(current_buffer)
                    })
                
                # Split the long paragraph using character-based chunking
                i = 0
                while i < len(para_text):
                    end_pos = min(i + chunk_size, len(para_text))
                    
                    # Try to find a sentence boundary if not at end
                    if end_pos < len(para_text):
                        sentence_end = max(
                            para_text.rfind('. ', i, end_pos),
                            para_text.rfind('! ', i, end_pos),
                            para_text.rfind('? ', i, end_pos),
                            para_text.rfind('.\n', i, end_pos),
                            para_text.rfind('!\n', i, end_pos),
                            para_text.rfind('?\n', i, end_pos)
                        )
                        if sentence_end > i:
                            end_pos = sentence_end + 2
                    
                    chunk_text = para_text[i:end_pos]
                    chunks.append({
                        'content': chunk_text,
                        'index': len(chunks),
                        'start_char': para_original_pos + i,
                        'end_char': para_original_pos + end_pos
                    })
                    
                    # Move to next chunk with overlap (same logic as character-based chunking)
                    i = end_pos - overlap if overlap < (end_pos - i) else i + 1
                
                # Reset buffer for next paragraphs
                current_buffer = ""
                buffer_start_pos = para_original_pos + len(para_text)
                
            else:
                # Try to add paragraph to current buffer
                separator = "\n\n" if current_buffer else ""
                potential_buffer = current_buffer + separator + para_text
                
                # If buffer would overflow, finalize it and start new buffer
                if len(potential_buffer) > chunk_size and current_buffer:
                    # Finalize current buffer as a chunk
                    chunks.append({
                        'content': current_buffer,
                        'index': len(chunks),
                        'start_char': buffer_start_pos,
                        'end_char': buffer_start_pos + len(current_buffer)
                    })
                    
                    # Calculate overlap and start new buffer
                    if overlap > 0 and len(current_buffer) > overlap:
                        # Try to find a sentence break in the overlap region
                        overlap_text = current_buffer[-overlap:]
                        sentence_breaks = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
                        
                        last_break_pos = -1
                        for break_char in sentence_breaks:
                            pos = overlap_text.rfind(break_char)
                            if pos > last_break_pos:
                                last_break_pos = pos
                        
                        if last_break_pos > 0:
                            # Use sentence break for overlap
                            overlap_start = len(current_buffer) - overlap + last_break_pos + 2
                            current_buffer = current_buffer[overlap_start:]
                            buffer_start_pos = buffer_start_pos + overlap_start
                        else:
                            # Use regular overlap
                            current_buffer = current_buffer[-overlap:]
                            buffer_start_pos = buffer_start_pos + len(current_buffer) - overlap
                    else:
                        # No overlap, start fresh
                        current_buffer = ""
                        buffer_start_pos = para_original_pos
                    
                    # Add current paragraph to new buffer
                    if current_buffer:
                        current_buffer += "\n\n" + para_text
                    else:
                        current_buffer = para_text
                        buffer_start_pos = para_original_pos
                else:
                    # Add paragraph to current buffer
                    current_buffer = potential_buffer
                    if not chunks and not current_buffer.startswith(para_text):
                        # This handles the first paragraph case
                        buffer_start_pos = para_original_pos
        
        # Add the final buffer if it has content
        if current_buffer:
            chunks.append({
                'content': current_buffer,
                'index': len(chunks),
                'start_char': buffer_start_pos,
                'end_char': buffer_start_pos + len(current_buffer)
            })
    
    else:
        # Simpler character-based chunking with improved sentence boundary respect
        i = 0
        while i < len(text):
            # Determine end position for this chunk
            end_pos = min(i + chunk_size, len(text))
            
            # If we're not at the end of the text and not at a natural boundary,
            # try to find a sentence boundary
            if end_pos < len(text):
                # Look for sentence boundaries (., !, ?)
                sentence_end = max(
                    text.rfind('. ', i, end_pos),
                    text.rfind('! ', i, end_pos),
                    text.rfind('? ', i, end_pos),
                    text.rfind('.\n', i, end_pos),
                    text.rfind('!\n', i, end_pos),
                    text.rfind('?\n', i, end_pos)
                )
                
                # If we found a sentence boundary, use it
                if sentence_end > i:
                    # +2 to include the sentence-ending punctuation and space
                    end_pos = sentence_end + 2
            
            # Create the chunk
            chunk_text = text[i:end_pos]
            chunks.append({
                'content': chunk_text,
                'index': len(chunks),
                'start_char': i,
                'end_char': end_pos
            })
            
            # Move to the next chunk, accounting for overlap
            i = end_pos - overlap if overlap < (end_pos - i) else i + 1
    
    logger.info(f"Created {len(chunks)} chunks from text")
    return chunks
