"""
Domain Mapping UI Components
Individual components for the domain priming workflow
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import tempfile
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SampleUploadComponent:
    """Component for uploading and processing sample PDF articles"""
    
    def __init__(self):
        # Import PDF processor function
        from src.pdf_processor import extract_text_from_pdf
        self.extract_text_from_pdf = extract_text_from_pdf
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render upload interface
        
        Returns:
            Dict with 'files' and 'texts' keys if successful, None otherwise
        """
        st.subheader("📁 Upload Sample Articles")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose PDF files (1-5 samples)",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload 1-5 representative articles from your research domain"
        )
        
        if not uploaded_files:
            st.info("👆 Upload sample PDF articles to get started")
            return None
        
        # Validate file count
        if len(uploaded_files) > 5:
            st.error("❌ Please upload maximum 5 files")
            return None
        
        # Display uploaded files
        st.write(f"**Uploaded {len(uploaded_files)} files:**")
        for i, file in enumerate(uploaded_files, 1):
            file_size = len(file.getvalue()) / 1024 / 1024  # MB
            st.write(f"{i}. {file.name} ({file_size:.1f} MB)")
        
        # Process files button
        if st.button("🔄 Process Articles", type="primary"):
            return self._process_files(uploaded_files)
        
        return None
    
    def _process_files(self, uploaded_files) -> Dict[str, Any]:
        """Process uploaded PDF files to extract text"""
        try:
            extracted_texts = []
            file_info = []
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i) / len(uploaded_files))
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Extract text using PDF processor
                    extracted_text = self.extract_text_from_pdf(tmp_path)
                    
                    if extracted_text and len(extracted_text.strip()) > 100:
                        extracted_texts.append(extracted_text)
                        file_info.append({
                            'name': uploaded_file.name,
                            'size': len(uploaded_file.getvalue()),
                            'text_length': len(extracted_text),
                            'word_count': len(extracted_text.split())
                        })
                        st.write(f"✅ {uploaded_file.name}: {len(extracted_text.split())} words extracted")
                    else:
                        st.warning(f"⚠️ {uploaded_file.name}: Minimal text extracted")
                
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    logger.error(f"PDF processing error for {uploaded_file.name}: {e}")
                
                finally:
                    # Clean up temporary file
                    Path(tmp_path).unlink(missing_ok=True)
            
            # Complete progress
            progress_bar.progress(1.0)
            status_text.text("Processing complete!")
            
            if not extracted_texts:
                st.error("❌ No text could be extracted from the uploaded files")
                return None
            
            # Display extraction summary
            st.success(f"✅ Successfully processed {len(extracted_texts)} articles")
            
            # Show extraction statistics
            with st.expander("📊 Extraction Statistics"):
                df = pd.DataFrame(file_info)
                st.dataframe(df, use_container_width=True)
                
                total_words = sum(info['word_count'] for info in file_info)
                st.metric("Total Words Extracted", f"{total_words:,}")
            
            return {
                'files': file_info,
                'texts': extracted_texts
            }
            
        except Exception as e:
            st.error(f"❌ Error during file processing: {str(e)}")
            logger.error(f"File processing error: {e}")
            return None

class DomainAnalysisComponent:
    """Component for running pattern analysis on sample texts"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def render(self, sample_texts: List[str]) -> Optional[Dict[str, Any]]:
        """
        Render analysis interface
        
        Args:
            sample_texts: List of extracted text from samples
            
        Returns:
            Domain profile dict if successful, None otherwise
        """
        st.subheader("🔍 Pattern Analysis")
        
        if not sample_texts:
            st.warning("⚠️ No sample texts available for analysis")
            return None
        
        # Display sample info
        st.write(f"**Ready to analyze {len(sample_texts)} sample articles**")
        total_words = sum(len(text.split()) for text in sample_texts)
        st.metric("Total Words to Analyze", f"{total_words:,}")
        
        # Domain name input
        domain_name = st.text_input(
            "Domain Profile Name",
            value=f"domain_profile_{datetime.now().strftime('%Y%m%d_%H%M')}",
            help="Give your domain profile a descriptive name"
        )
        
        if not domain_name.strip():
            st.error("❌ Please provide a domain name")
            return None
        
        # Analysis options
        with st.expander("⚙️ Analysis Options"):
            enhance_with_llm = st.checkbox(
                "Enhance with LLM", 
                value=True,
                help="Use LLM to enhance pattern detection with semantic understanding"
            )
            
            min_frequency = st.slider(
                "Minimum Term Frequency",
                min_value=1,
                max_value=5,
                value=2,
                help="Minimum times a term must appear to be considered significant"
            )
        
        # Run analysis button
        if st.button("🚀 Run Analysis", type="primary"):
            return self._run_analysis(sample_texts, domain_name.strip(), enhance_with_llm, min_frequency)
        
        return None
    
    def _run_analysis(self, sample_texts: List[str], domain_name: str, enhance_with_llm: bool, min_frequency: int) -> Optional[Dict[str, Any]]:
        """Run the domain analysis workflow"""
        try:
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Pattern Detection
            status_text.text("🔍 Detecting patterns and terms...")
            progress_bar.progress(0.2)
            
            # Run basic pattern analysis
            domain_profile = self.engine.analyze_sample_articles(
                sample_texts,
                domain_name=domain_name,
                enhance_with_llm=False,  # Do basic analysis first
                min_frequency=min_frequency
            )
            
            progress_bar.progress(0.5)
            
            # Step 2: LLM Enhancement (if enabled)
            if enhance_with_llm:
                status_text.text("🤖 Enhancing with LLM semantic understanding...")
                
                # Get raw patterns for LLM enhancement
                raw_patterns = domain_profile.get('raw_patterns', {})
                
                # Run LLM enhancement
                enhanced_patterns = self.engine.term_mapper.enhance_patterns_with_llm(raw_patterns)
                
                # Update domain profile with enhanced patterns
                domain_profile['enhanced_patterns'] = enhanced_patterns
                domain_profile['domain_map'] = self.engine._merge_patterns_into_domain_map(
                    raw_patterns, enhanced_patterns
                )
                
                progress_bar.progress(0.8)
            
            # Step 3: Finalize
            status_text.text("✅ Analysis complete!")
            progress_bar.progress(1.0)
            
            # Display results summary
            self._display_analysis_summary(domain_profile)
            
            return domain_profile
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            logger.error(f"Domain analysis error: {e}")
            return None
    
    def _display_analysis_summary(self, domain_profile: Dict[str, Any]):
        """Display analysis results summary"""
        st.success("🎉 Analysis Complete!")
        
        # Extract key metrics
        metadata = domain_profile.get('metadata', {})
        domain_map = domain_profile.get('domain_map', {})
        raw_patterns = domain_profile.get('raw_patterns', {})
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Domain Mappings", len(domain_map))
        
        with col2:
            total_terms = sum(len(synonyms) for synonyms in domain_map.values())
            st.metric("Total Terms", total_terms)
        
        with col3:
            unique_terms = len(raw_patterns.get('term_frequencies', {}))
            st.metric("Unique Terms Found", unique_terms)
        
        # Show sample mappings
        if domain_map:
            with st.expander("🔍 Sample Domain Mappings"):
                # Show first 5 mappings as examples
                sample_mappings = dict(list(domain_map.items())[:5])
                for canonical, synonyms in sample_mappings.items():
                    st.write(f"**{canonical}:** {', '.join(synonyms[:3])}{'...' if len(synonyms) > 3 else ''}")
                
                if len(domain_map) > 5:
                    st.write(f"... and {len(domain_map) - 5} more mappings")

class DomainMapEditorComponent:
    """Component for editing and refining domain mappings"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def render(self, domain_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Render domain map editing interface
        
        Args:
            domain_profile: Current domain profile to edit
            
        Returns:
            Updated domain profile if changes made, None otherwise
        """
        st.subheader("✏️ Edit Domain Mappings")
        
        if not domain_profile:
            st.warning("⚠️ No domain profile available for editing")
            return None
        
        domain_map = domain_profile.get('domain_map', {})
        
        if not domain_map:
            st.warning("⚠️ No domain mappings found in profile")
            return None
        
        # Create tabs for different editing modes
        edit_tab, add_tab, delete_tab = st.tabs(["Edit Existing", "Add New", "Delete"])
        
        changes_made = False
        updated_profile = domain_profile.copy()
        
        with edit_tab:
            changes_made |= self._render_edit_existing(domain_map, updated_profile)
        
        with add_tab:
            changes_made |= self._render_add_new(domain_map, updated_profile)
        
        with delete_tab:
            changes_made |= self._render_delete_mappings(domain_map, updated_profile)
        
        # Apply changes button
        if changes_made:
            if st.button("💾 Apply Changes", type="primary"):
                return self._apply_changes(updated_profile)
        
        # Display current mappings
        self._display_current_mappings(domain_map)
        
        return None
    
    def _render_edit_existing(self, domain_map: Dict[str, List[str]], updated_profile: Dict[str, Any]) -> bool:
        """Render interface for editing existing mappings"""
        st.write("**Edit Existing Mappings:**")
        
        if not domain_map:
            st.info("No mappings to edit")
            return False
        
        # Select mapping to edit
        mapping_names = list(domain_map.keys())
        selected_mapping = st.selectbox("Select mapping to edit:", mapping_names)
        
        if selected_mapping:
            current_synonyms = domain_map[selected_mapping]
            
            # Edit canonical term
            new_canonical = st.text_input(
                "Canonical term:",
                value=selected_mapping,
                key=f"edit_canonical_{selected_mapping}"
            )
            
            # Edit synonyms
            synonyms_text = ", ".join(current_synonyms)
            new_synonyms_text = st.text_area(
                "Synonyms (comma-separated):",
                value=synonyms_text,
                key=f"edit_synonyms_{selected_mapping}",
                help="Enter synonyms separated by commas"
            )
            
            # Check for changes
            new_synonyms = [s.strip() for s in new_synonyms_text.split(',') if s.strip()]
            
            if new_canonical != selected_mapping or new_synonyms != current_synonyms:
                st.info("✏️ Changes detected for this mapping")
                
                if st.button(f"Update '{selected_mapping}'", key=f"update_{selected_mapping}"):
                    # Apply the edit
                    new_domain_map = updated_profile['domain_map'].copy()
                    
                    # Remove old mapping
                    if selected_mapping in new_domain_map:
                        del new_domain_map[selected_mapping]
                    
                    # Add new mapping
                    new_domain_map[new_canonical] = new_synonyms
                    updated_profile['domain_map'] = new_domain_map
                    
                    st.success(f"✅ Updated mapping: {new_canonical}")
                    return True
        
        return False
    
    def _render_add_new(self, domain_map: Dict[str, List[str]], updated_profile: Dict[str, Any]) -> bool:
        """Render interface for adding new mappings"""
        st.write("**Add New Mapping:**")
        
        # Input fields
        new_canonical = st.text_input(
            "Canonical term:",
            key="new_canonical",
            help="The main/preferred term"
        )
        
        new_synonyms_text = st.text_input(
            "Synonyms (comma-separated):",
            key="new_synonyms",
            help="Alternative terms that mean the same thing"
        )
        
        if new_canonical and new_synonyms_text:
            new_synonyms = [s.strip() for s in new_synonyms_text.split(',') if s.strip()]
            
            if new_canonical in domain_map:
                st.warning(f"⚠️ Mapping for '{new_canonical}' already exists")
            else:
                if st.button("➕ Add Mapping", key="add_new_mapping"):
                    # Add new mapping
                    new_domain_map = updated_profile['domain_map'].copy()
                    new_domain_map[new_canonical] = new_synonyms
                    updated_profile['domain_map'] = new_domain_map
                    
                    st.success(f"✅ Added new mapping: {new_canonical} → {', '.join(new_synonyms)}")
                    return True
        
        return False
    
    def _render_delete_mappings(self, domain_map: Dict[str, List[str]], updated_profile: Dict[str, Any]) -> bool:
        """Render interface for deleting mappings"""
        st.write("**Delete Mappings:**")
        
        if not domain_map:
            st.info("No mappings to delete")
            return False
        
        # Multi-select for deletion
        mappings_to_delete = st.multiselect(
            "Select mappings to delete:",
            list(domain_map.keys()),
            key="delete_mappings"
        )
        
        if mappings_to_delete:
            st.warning(f"⚠️ This will delete {len(mappings_to_delete)} mapping(s)")
            
            if st.button("🗑️ Delete Selected", key="confirm_delete"):
                # Delete selected mappings
                new_domain_map = updated_profile['domain_map'].copy()
                
                for mapping in mappings_to_delete:
                    if mapping in new_domain_map:
                        del new_domain_map[mapping]
                
                updated_profile['domain_map'] = new_domain_map
                
                st.success(f"✅ Deleted {len(mappings_to_delete)} mapping(s)")
                return True
        
        return False
    
    def _apply_changes(self, updated_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Apply changes to the domain profile"""
        try:
            # Update metadata
            updated_profile['metadata']['user_refined'] = True
            updated_profile['metadata']['last_refined'] = datetime.now().isoformat()
            
            # Use engine to properly refine the profile
            refined_profile = self.engine.review_and_refine_domain_map(
                user_modifications={'profile': updated_profile},
                save_profile=False
            )
            
            st.success("✅ Changes applied successfully!")
            return refined_profile
            
        except Exception as e:
            st.error(f"❌ Error applying changes: {str(e)}")
            logger.error(f"Error applying domain map changes: {e}")
            return None
    
    def _display_current_mappings(self, domain_map: Dict[str, List[str]]):
        """Display current domain mappings in a table"""
        if not domain_map:
            return
        
        with st.expander(f"📋 Current Domain Mappings ({len(domain_map)} total)"):
            # Convert to DataFrame for display
            mapping_data = []
            for canonical, synonyms in domain_map.items():
                mapping_data.append({
                    'Canonical Term': canonical,
                    'Synonyms': ', '.join(synonyms),
                    'Count': len(synonyms)
                })
            
            df = pd.DataFrame(mapping_data)
            st.dataframe(df, use_container_width=True)

class ProfileManagerComponent:
    """Component for managing domain profiles (save/load/delete)"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def render(self, current_profile: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Render profile management interface
        
        Args:
            current_profile: Currently active domain profile
            
        Returns:
            Dict with action info if action performed, None otherwise
        """
        st.subheader("💾 Manage Domain Profiles")
        
        # Create tabs for different management operations
        save_tab, load_tab, list_tab = st.tabs(["Save Profile", "Load Profile", "Profile List"])
        
        result = None
        
        with save_tab:
            result = self._render_save_profile(current_profile)
        
        with load_tab:
            result = self._render_load_profile()
        
        with list_tab:
            self._render_profile_list()
        
        return result
    
    def _render_save_profile(self, current_profile: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Render save profile interface"""
        st.write("**Save Current Profile:**")
        
        if not current_profile:
            st.warning("⚠️ No profile to save. Complete analysis first.")
            return None
        
        # Get current profile name
        current_name = current_profile.get('metadata', {}).get('domain_name', '')
        
        # Profile name input
        profile_name = st.text_input(
            "Profile Name:",
            value=current_name,
            key="save_profile_name",
            help="Choose a descriptive name for this domain profile"
        )
        
        if not profile_name.strip():
            st.error("❌ Please provide a profile name")
            return None
        
        # Display profile summary
        domain_map = current_profile.get('domain_map', {})
        metadata = current_profile.get('metadata', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Domain Mappings", len(domain_map))
        with col2:
            st.metric("Sample Articles", metadata.get('sample_count', 0))
        
        # Save button
        if st.button("💾 Save Profile", type="primary", key="save_profile_btn"):
            try:
                # Update profile name in metadata
                updated_profile = current_profile.copy()
                updated_profile['metadata']['domain_name'] = profile_name.strip()
                
                # Save using engine
                self.engine.current_domain_profile = updated_profile
                saved_path = self.engine.save_domain_profile()
                
                st.success(f"✅ Profile saved successfully!")
                st.info(f"📁 Saved to: {saved_path}")
                
                return {
                    'action': 'saved',
                    'name': profile_name.strip(),
                    'path': saved_path
                }
                
            except Exception as e:
                st.error(f"❌ Error saving profile: {str(e)}")
                logger.error(f"Profile save error: {e}")
        
        return None
    
    def _render_load_profile(self) -> Optional[Dict[str, Any]]:
        """Render load profile interface"""
        st.write("**Load Existing Profile:**")
        
        try:
            # Get available profiles
            available_profiles = self.engine.list_available_profiles()
            
            if not available_profiles:
                st.info("📝 No saved profiles found")
                return None
            
            # Profile selection
            profile_options = {
                f"{profile['domain_name']} ({profile['created_at'][:10]})": profile
                for profile in available_profiles
            }
            
            selected_option = st.selectbox(
                "Select profile to load:",
                list(profile_options.keys()),
                key="load_profile_select"
            )
            
            if selected_option:
                selected_profile_info = profile_options[selected_option]
                
                # Display profile details
                with st.expander("📊 Profile Details"):
                    st.write(f"**Name:** {selected_profile_info['domain_name']}")
                    st.write(f"**Created:** {selected_profile_info['created_at']}")
                    st.write(f"**Mappings:** {selected_profile_info['mapping_count']}")
                    st.write(f"**Samples:** {selected_profile_info['sample_count']}")
                
                # Load button
                if st.button("📂 Load Profile", type="primary", key="load_profile_btn"):
                    try:
                        profile_path = selected_profile_info['file_path']
                        loaded_profile = self.engine.load_domain_profile(profile_path)
                        
                        st.success(f"✅ Profile '{selected_profile_info['domain_name']}' loaded successfully!")
                        
                        return {
                            'action': 'loaded',
                            'profile': loaded_profile,
                            'name': selected_profile_info['domain_name']
                        }
                        
                    except Exception as e:
                        st.error(f"❌ Error loading profile: {str(e)}")
                        logger.error(f"Profile load error: {e}")
        
        except Exception as e:
            st.error(f"❌ Error accessing profiles: {str(e)}")
            logger.error(f"Profile access error: {e}")
        
        return None
    
    def _render_profile_list(self):
        """Render list of all available profiles"""
        st.write("**Available Profiles:**")
        
        try:
            available_profiles = self.engine.list_available_profiles()
            
            if not available_profiles:
                st.info("📝 No saved profiles found")
                return
            
            # Create DataFrame for display
            profile_data = []
            for profile in available_profiles:
                profile_data.append({
                    'Name': profile['domain_name'],
                    'Created': profile['created_at'][:10],
                    'Mappings': profile['mapping_count'],
                    'Samples': profile['sample_count'],
                    'Size': f"{profile['file_size'] / 1024:.1f} KB"
                })
            
            df = pd.DataFrame(profile_data)
            st.dataframe(df, use_container_width=True)
            
            # Export functionality
            if st.button("📤 Export All Profiles Info"):
                export_data = {
                    'profiles': available_profiles,
                    'exported_at': datetime.now().isoformat(),
                    'total_profiles': len(available_profiles)
                }
                
                st.download_button(
                    label="💾 Download Profile Info (JSON)",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"domain_profiles_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
        
        except Exception as e:
            st.error(f"❌ Error listing profiles: {str(e)}")
            logger.error(f"Profile listing error: {e}")