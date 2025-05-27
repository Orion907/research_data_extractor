# tests/test_picots_parser.py
"""
Test module for PICOTS parser functionality
"""
import os
import sys
import unittest
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.utils.picots_parser import PicotsParser, PicotsData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPicotsParser(unittest.TestCase):
    """Test cases for PICOTS parser functionality"""
    
    def setUp(self):
        """Set up test case"""
        self.parser = PicotsParser()
        
        # Full PICOTS table from actual research protocol
        self.full_picots_table = """Table 1. Preliminary PICOTS criteria
	Inclusion Criteria	Exclusion Criteria
Population 	KQ 1. Children and adolescents aged 3 to 18 years without known anxiety and depression

KQ 2. Children and adolescents aged 3 to 18 years with a diagnosis of depression or anxiety

KQ 3. Children and adolescents aged 3 to 18 years with a chronic condition who are at risk for elevated symptoms of or being diagnosed with anxiety and depression 

Definition of chronic physical conditions: Medical physical conditions (i.e., conditions that primarily affect the body's systems and functions) that persist for one year or longer and require ongoing medical attention, limit activities of daily living, or both.	Studies with ≥20% of participants in the following groups and do not report findings by population
- In institutions (e.g., psychiatric inpatients, long-term care facilities)
- Diagnosed with advanced neurodevelopmental disorders (e.g., severe autism spectrum disorders [for example, level 3 on DSM-5], severe attention-deficit/hyperactivity disorder [e.g., based on DSM-5 definition], severe learning disorders [e.g., more than 2 standard deviations below the mean in one or more areas of cognitive processing related to the specific learning disorder])
- With major behavioral or emotional dysregulation (e.g., conduct disorder, oppositional defiant disorder, disruptive mood dysregulation disorder)a
- With substance use disorder

We will exclude studies with MBIs designed and/or administered only to parents/caregivers, as well as interventions administered by parents/caregivers.

We will exclude studies designed to treat test or sports performance anxiety, anxiety associated with medical/dental procedures and with interventions for specific high-risk exposures such as for post-sexual assault or another traumatic event.
Interventions 	KQ 1–3
In addition to the minimum requirements identified above: 
- Mindfulness-based intervention, provided alone or in addition to other therapies
- Mindfulness is the primary component for multicomponent interventions (as a part of behavioral and similar non-pharmacological strategies), meaning that the intervention must be centered around mindfulness (e.g., the majority of the sessions or focus are mindfulness-based).
- A mindfulness instructor (e.g., therapist, teacher) must have some training in providing mindfulness. We do not specify the required minimum training.
- Clear specification of repeated practice (e.g., more than one session with an instructor, or repeated self-directed exercises after at least one initial session with an instructor). 

Examples of other therapies include structured mindfulness programs and mindfulness-based therapies such as:
- Mindfulness-based Stress Reduction
- Mindfulness-based Cognitive Therapy
- Acceptance and Commitment Therapy
Components of programs, if they are intentionally used to promote mindfulness principles and meet other criteria, may include:
- Relaxation techniques 
- Meditation 
- Mindful breathing
- Guided imagery 
- Visualization	Pharmacologic interventions or traditional psychotherapies alone (e.g., cognitive-behavioral therapy, play therapy, dialectical behavior therapy, parent-child interaction therapy) and integrative therapies alone including acupuncture/acupressure, expressive therapies, exercise, yoga, Tai Chi, biofeedback, hypnotherapy, massage, chiropractic care, homeopathy, diets (e.g., gluten-free diet), traditional Chinese medicine, Ayurveda.
Comparators	KQ 1. Usual care, enhanced usual care, waitlist control, sham, attention control, or no active intervention.

KQ 2–3. Usual care, enhanced usual care, waitlist control, sham, attention control, no active intervention, or conventional therapies (i.e., pharmacotherapy for anxiety and/or depression, behavioral interventionsb) 	Other mindfulness-based interventions (i.e., comparative effectiveness of MBIs). 
Other interventions not listed in the "included" list.
Outcomes 	KQ 1–3
Primary outcomes (children and adolescent outcomes)
- Quality of life (e.g., PedsQL, KIDSCREEN, CHQ, ITQOL, PQ-LES-Q)
- General and social functioning (e.g., SDQ, SSIS, CGI-I, CGAS), including behavior problems (e.g., ECBI, CBCL, SDQ), coping skills (e.g., CSI-CA, CCSC, RSQ), executive functioning (e.g., BRIEF), academic performance (e.g., WIAT, Woodcock-Johnson Tests of Achievement)
- Disability (e.g., VABS, FDI, days of missed school)
- Depression (e.g., CDI, BDI, MFQ, CES-D, CDRS-R, RADS, PHQ-A, PI-ED), diagnosis (KQs 2 and 3 only), and remission and response (KQs 1 and 3)
- Anxiety (e.g., SCARED, MASC, SCAS, CAIS, GAD-7, PHQ-A, PI-ED), diagnosis (KQs 2 and 3 only), and remission and response (KQs 1 and 3)
- Any reported adverse events or unintended negative consequences attributed to treatment

Additional outcomes (children and adolescent outcomes)
- Acceptance of experiences in the present moment (e.g., CAMM)
- Autonomic arousal (e.g., SCL, HRV)
- Executive functioning (e.g., BRIEF)
- Subjective well-being (e.g., PANAS-C, SLSS)
- Substance use
- Psychological flexibility (e.g., AFQ-Y, AAQ)
- Healthcare utilization	Other outcomes, patient/caregiver outcomes
Timing 	•	A minimum of 4 weeks since the beginning of the intervention or baseline assessment (if the intervention start cannot be determined) for all outcomes except for harms. 
- We will extract harms reported at any followup, regardless of the duration since the intervention start or baseline assessment.	Mid-intervention assessment times
Setting 	KQ 1–3
- Administered in outpatient health care or community settings (e.g., schools, residential)
- Trials conducted in countries rated as "very high" on the 2019 Human Development Index (as defined by the United Nations Development Program)	In-patient, ED/EMS, and psychiatric subacute settings (e.g., partial hospitalization programs, intensive outpatient programs)
Study Design 	•	Randomized controlled trials (individually or site-randomized), with individually randomized trials reporting outcomes for a minimum of 10 participants per treatment arm 
- Period 1 data from crossover RCTs
- Published in English-language
- Published in 2009 or later	Other 
Abbreviations: AAQ = Acceptance and Action Questionnaire; AFQ-Y = Avoidance and Fusion Questionnaire for Youth; BDI = Beck Depression Inventory; BRIEF = Behavior Rating Inventory of Executive Function; CAIS = Child Anxiety Impact Scale; CAMM = Child and Adolescent Mindfulness Measure; CBCL = Child Behavior Checklist; CCSC = Children's Coping Strategies Checklist; CDI = Children's Depression Inventory; CDRS-R = Children's Depression Rating Scale–Revised; CES-D = Center for Epidemiologic Studies Depression Scale; CGAS = Children's Global Assessment Scale; CGI-I = Clinical Global Impression-Improvement Scale; CHQ = Child Health Questionnaire; CSI-CA = Coping Strategies Inventory for Children and Adolescents; ED/EMS = emergency department /emergency medical services; ECBI = Eyberg Child Behavior Inventory; FDI = Functional Disability Inventory Child Form; GAD-7 = Generalized Anxiety Disorder scale; HRV = heart rate variability; ITQOL = Infant/Toddler Quality of Life Questionnaire; KQ = Key Question; MASC = Multidimensional Anxiety Scale for Children; MFQ = Mood and Feelings Questionnaire; NA = not applicable; PedsQL = Pediatric Quality of Life Inventory; PHQ-A = Patient Health Questionnaire for Adolescents; PICOTS = population, interventions, comparators, outcomes, timing, and setting; PI-ED = Paediatric Index of Emotional Distress; PQ-LES-Q = Perceived Quality of Life Scale; RADS = Reynolds Adolescent Depression Scale; RSQ = Responses to Stress Questionnaire; SCARED = Screen for Child Anxiety Related Emotional Disorders; SCAS = Spence Children's Anxiety Scale; SCL = Skin Conductance Level; SDQ = Strengths and Difficulties Questionnaire; SLSS = Students' Life Satisfaction Scale; SSIS = Social Skills Improvement System; PANAS-C = Positive and Negative Affect Schedule for Children; SWLS = Satisfaction with Life Scale; VABS = Vineland Adaptive Behavior Scales; WIAT = Wechsler Individual Achievement Test; WISC = Wechsler Intelligence Scale for Children"""
        
        # Sample Key Questions for testing
        self.sample_key_questions = """**Key Question 1.** What are the benefits and harms of mindfulness-based interventions in the general child and adolescent populations?
**Key Question 2.** What are the benefits and harms of mindfulness-based interventions in children and adolescents diagnosed with anxiety and/or depression?
**Key Question 3.** What are the benefits and harms of mindfulness-based interventions in children and adolescents with a chronic condition who are at risk for elevated symptoms of anxiety and/or depression?"""
    
    def test_parse_full_picots_table(self):
        """Test parsing the complete PICOTS table"""
        result = self.parser.parse_picots_table(self.full_picots_table)
        
        # Verify basic structure
        self.assertIsInstance(result, PicotsData)
        
        # Verify detected KQs
        self.assertIsNotNone(result.detected_kqs)
        self.assertGreater(len(result.detected_kqs), 0)
        
        logger.info(f"Detected {len(result.detected_kqs)} Key Questions")
    
    def test_population_parsing(self):
        """Test parsing of Population section"""
        result = self.parser.parse_picots_table(self.full_picots_table)
        
        # Should extract 3 KQ population criteria
        self.assertEqual(len(result.population), 3)
        
        # Check that all KQs are represented
        population_text = ' '.join(result.population)
        self.assertIn('KQ 1', population_text)
        self.assertIn('KQ 2', population_text)
        self.assertIn('KQ 3', population_text)
        
        logger.info(f"Population criteria: {result.population}")
    
    def test_interventions_parsing(self):
        """Test parsing of Interventions section"""
        result = self.parser.parse_picots_table(self.full_picots_table)
        
        # Should have intervention criteria
        self.assertGreater(len(result.interventions), 0)
        
        # Check for key intervention concepts
        interventions_text = ' '.join(result.interventions)
        self.assertIn('mindfulness', interventions_text.lower())
        
        logger.info(f"Found {len(result.interventions)} intervention criteria")
    
    def test_outcomes_parsing(self):
        """Test parsing of Outcomes section"""
        result = self.parser.parse_picots_table(self.full_picots_table)
        
        # Should have outcome criteria
        self.assertGreater(len(result.outcomes), 0)
        
        # Check for key outcome concepts
        outcomes_text = ' '.join(result.outcomes)
        self.assertIn('quality of life', outcomes_text.lower())
        self.assertIn('depression', outcomes_text.lower())
        self.assertIn('anxiety', outcomes_text.lower())
        
        logger.info(f"Found {len(result.outcomes)} outcome criteria")
    
    def test_abbreviations_parsing(self):
        """Test parsing of abbreviations section"""
        result = self.parser.parse_picots_table(self.full_picots_table)
        
        # Should have abbreviations
        self.assertIsNotNone(result.abbreviations)
        self.assertGreater(len(result.abbreviations), 0)
        
        # Check for specific abbreviations
        self.assertIn('KQ', result.abbreviations)
        self.assertEqual(result.abbreviations['KQ'], 'Key Question')
        
        self.assertIn('PICOTS', result.abbreviations)
        
        logger.info(f"Parsed {len(result.abbreviations)} abbreviations")
    
    def test_key_questions_parsing(self):
        """Test parsing separate key questions"""
        result = self.parser.parse_picots_table(
            self.full_picots_table, 
            key_questions=self.sample_key_questions
        )
        
        # Should have separate key questions
        self.assertIsNotNone(result.key_questions)
        self.assertEqual(len(result.key_questions), 3)
        
        # Check content
        kq_text = ' '.join(result.key_questions)
        self.assertIn('mindfulness-based interventions', kq_text)
        self.assertIn('general child and adolescent populations', kq_text)
        
        logger.info(f"Parsed {len(result.key_questions)} separate key questions")
    
    def test_empty_input(self):
        """Test handling of empty input"""
        result = self.parser.parse_picots_table("")
        
        # Should return valid but empty structure
        self.assertIsInstance(result, PicotsData)
        self.assertEqual(len(result.population), 0)
        self.assertEqual(len(result.interventions), 0)
    
    def test_malformed_input(self):
        """Test handling of malformed input"""
        malformed_table = "This is not a proper PICOTS table format"
        
        # Should not crash
        result = self.parser.parse_picots_table(malformed_table)
        self.assertIsInstance(result, PicotsData)

if __name__ == "__main__":
    unittest.main()