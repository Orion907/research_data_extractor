"""
Module for chunking text for LLM processing.
"""
import logging

# Configure logging
logger = logging.getLogger(__name__)

def _find_sentence_boundary(text, start, end):
    """
    Find the best sentence boundary within the given range.
    
    Args:
        text (str): The text to search
        start (int): Start position
        end (int): End position
        
    Returns:
        int: Position of sentence boundary, or -1 if none found
    """
    sentence_breaks = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    
    best_pos = -1
    for break_char in sentence_breaks:
        pos = text.rfind(break_char, start, end)
        if pos > best_pos:
            best_pos = pos
    
    return best_pos + 2 if best_pos > start else -1

def _filter_paragraphs_with_positions(text):
    """
    Split text by paragraphs and track their positions in the original text.
    
    Args:
        text (str): The text to process
        
    Returns:
        list: List of tuples (paragraph_text, original_position)
    """
    paragraphs = text.split('\n\n')
    filtered_paragraphs = []
    current_pos = 0
    
    for para in paragraphs:
        para_stripped = para.strip()
        if para_stripped:
            # Find the actual start position of this paragraph in the original text
            para_start = text.find(para_stripped, current_pos)
            filtered_paragraphs.append((para_stripped, para_start))
            current_pos = para_start + len(para_stripped)
    
    return filtered_paragraphs

def _create_chunk(content, index, start_char, end_char):
    """
    Create a standardized chunk dictionary.
    
    Args:
        content (str): The chunk content
        index (int): Chunk index
        start_char (int): Starting character position
        end_char (int): Ending character position
        
    Returns:
        dict: Chunk dictionary
    """
    return {
        'content': content,
        'index': index,
        'start_char': start_char,
        'end_char': end_char
    }

def _handle_long_paragraph(para_text, para_original_pos, chunk_size, overlap, chunks):
    """
    Handle paragraphs that are longer than chunk_size by splitting them.
    
    Args:
        para_text (str): The paragraph text
        para_original_pos (int): Original position in full text
        chunk_size (int): Maximum chunk size
        overlap (int): Overlap between chunks
        chunks (list): List to append chunks to
    """
    i = 0
    while i < len(para_text):
        end_pos = min(i + chunk_size, len(para_text))
        
        # Try to find a sentence boundary if not at end
        if end_pos < len(para_text):
            boundary = _find_sentence_boundary(para_text, i, end_pos)
            if boundary > 0:
                end_pos = boundary
        
        chunk_text = para_text[i:end_pos]
        chunks.append(_create_chunk(
            chunk_text,
            len(chunks),
            para_original_pos + i,
            para_original_pos + end_pos
        ))
        
        # Move to next chunk with overlap (use original logic)
        if end_pos < len(para_text):
            i = max(end_pos - overlap, i + 1)
        else:
            break

def _calculate_buffer_overlap(current_buffer, overlap):
    """
    Calculate overlap for buffer using sentence boundaries when possible.
    This preserves the original overlap logic for paragraph boundaries.
    
    Args:
        current_buffer (str): Current buffer content
        overlap (int): Desired overlap size
        
    Returns:
        str: Overlap text to use in next buffer
    """
    if overlap <= 0 or len(current_buffer) <= overlap:
        return ""
    
    # Try to find a sentence break in the overlap region (original logic)
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
        return current_buffer[overlap_start:]
    else:
        # Use regular overlap
        return current_buffer[-overlap:]

def _chunk_with_paragraphs(text, chunk_size, overlap):
    """
    Chunk text while respecting paragraph boundaries.
    This preserves the original complex overlap logic between paragraphs.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Maximum chunk size
        overlap (int): Overlap between chunks
        
    Returns:
        list: List of chunks
    """
    chunks = []
    filtered_paragraphs = _filter_paragraphs_with_positions(text)
    
    current_buffer = ""
    buffer_start_pos = 0
    
    for para_text, para_original_pos in filtered_paragraphs:
        # Handle long paragraphs separately
        if len(para_text) > chunk_size:
            # First, finalize any existing buffer
            if current_buffer:
                chunks.append(_create_chunk(
                    current_buffer,
                    len(chunks),
                    buffer_start_pos,
                    buffer_start_pos + len(current_buffer)
                ))
            
            # Split the long paragraph
            _handle_long_paragraph(para_text, para_original_pos, chunk_size, overlap, chunks)
            
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
                chunks.append(_create_chunk(
                    current_buffer,
                    len(chunks),
                    buffer_start_pos,
                    buffer_start_pos + len(current_buffer)
                ))
                
                # Calculate overlap and start new buffer (preserve original logic)
                if overlap > 0 and len(current_buffer) > overlap:
                    overlap_text = _calculate_buffer_overlap(current_buffer, overlap)
                    if overlap_text:
                        # Calculate how much of the original buffer we're keeping
                        overlap_start = len(current_buffer) - len(overlap_text)
                        current_buffer = overlap_text + "\n\n" + para_text
                        buffer_start_pos = buffer_start_pos + overlap_start
                    else:
                        current_buffer = para_text
                        buffer_start_pos = para_original_pos
                else:
                    # No overlap, start fresh
                    current_buffer = para_text
                    buffer_start_pos = para_original_pos
            else:
                # Add paragraph to current buffer
                current_buffer = potential_buffer
                if not chunks and not current_buffer.startswith(para_text):
                    buffer_start_pos = para_original_pos
    
    # Add final buffer if it has content
    if current_buffer:
        chunks.append(_create_chunk(
            current_buffer,
            len(chunks),
            buffer_start_pos,
            buffer_start_pos + len(current_buffer)
        ))
    
    return chunks

def _chunk_by_characters(text, chunk_size, overlap):
    """
    Chunk text using character-based approach with sentence boundary respect.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Maximum chunk size
        overlap (int): Overlap between chunks
        
    Returns:
        list: List of chunks
    """
    chunks = []
    i = 0
    
    while i < len(text):
        # Determine end position for this chunk
        end_pos = min(i + chunk_size, len(text))
        
        # If not at the end, try to find a sentence boundary
        if end_pos < len(text):
            boundary = _find_sentence_boundary(text, i, end_pos)
            if boundary > 0:
                end_pos = boundary
        
        # Create the chunk
        chunk_text = text[i:end_pos]
        chunks.append(_create_chunk(chunk_text, len(chunks), i, end_pos))
        
        # Move to the next chunk, accounting for overlap
        if end_pos < len(text):
            i = max(end_pos - overlap, i + 1)
        else:
            break
    
    return chunks

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
    
    if respect_paragraphs:
        chunks = _chunk_with_paragraphs(text, chunk_size, overlap)
    else:
        chunks = _chunk_by_characters(text, chunk_size, overlap)
    
    logger.info(f"Created {len(chunks)} chunks from text")
    return chunks