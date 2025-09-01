"""
Ontology manager for automatic RDF/TTL generation and updates.
Handles DPV+ODRL+ODRE ontology creation and maintenance.
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import urllib.parse

from .config import Config
from .models import LegislationRule, IntegratedRule
from .event_system import Event, event_bus

# Optional RDF library
try:
    import rdflib
    from rdflib import Graph, Namespace, URIRef, Literal, BNode
    from rdflib.namespace import RDF, RDFS, XSD
    RDF_AVAILABLE = True
except ImportError:
    RDF_AVAILABLE = False

logger = logging.getLogger(__name__)

class OntologyManager:
    """Manages automatic ontology generation and updates."""
    
    def __init__(self, standards_converter):
        self.standards_converter = standards_converter
        self.output_path = Config.STANDARDS_OUTPUT_PATH
        self.last_update = None
        self._ontology_cache: Dict[str, str] = {}
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        if not RDF_AVAILABLE:
            logger.warning("RDFLib not available. TTL generation will be limited.")
    
    def _safe_uri_encode(self, text: str) -> str:
        """Safely encode text for use in URIs."""
        if not text:
            return ""
        return urllib.parse.quote(text, safe='')
    
    async def update_single_rule(self, rule_data: Dict[str, Any], old_rule_data: Optional[Dict[str, Any]] = None) -> None:
        """Update ontology for a single rule change."""
        try:
            logger.info(f"Updating ontology for rule: {rule_data.get('id', 'unknown')}")
            
            # Convert rule data to LegislationRule
            rule = LegislationRule(**rule_data)
            
            # Convert to integrated format
            integrated_rule = self.standards_converter.json_rules_to_integrated(rule)
            
            # Update incremental files
            await self._update_incremental_ontology(integrated_rule, old_rule_data)
            
            # Publish event
            await event_bus.publish_event(Event(
                event_type="ontology_updated",
                data={
                    "rule_id": rule.id,
                    "update_type": "single_rule",
                    "timestamp": datetime.utcnow().isoformat()
                },
                source="ontology_manager"
            ))
            
            logger.info(f"Ontology updated successfully for rule: {rule.id}")
            
        except Exception as e:
            logger.error(f"Error updating ontology for single rule: {e}")
            raise
    
    async def remove_rule(self, rule_id: str) -> None:
        """Remove a rule from the ontology."""
        try:
            logger.info(f"Removing rule from ontology: {rule_id}")
            
            # Remove from incremental files
            await self._remove_rule_from_ontology(rule_id)
            
            # Publish event
            await event_bus.publish_event(Event(
                event_type="ontology_updated",
                data={
                    "rule_id": rule_id,
                    "update_type": "rule_removed",
                    "timestamp": datetime.utcnow().isoformat()
                },
                source="ontology_manager"
            ))
            
            logger.info(f"Rule removed from ontology successfully: {rule_id}")
            
        except Exception as e:
            logger.error(f"Error removing rule from ontology: {e}")
            raise
    
    async def regenerate_ontologies(self, rules_data: List[Dict[str, Any]]) -> None:
        """Regenerate complete ontologies from rule data."""
        try:
            logger.info(f"Regenerating complete ontologies for {len(rules_data)} rules")
            
            # Convert all rules
            legislation_rules = []
            integrated_rules = []
            
            for rule_data in rules_data:
                try:
                    rule = LegislationRule(**rule_data)
                    legislation_rules.append(rule)
                    
                    integrated_rule = self.standards_converter.json_rules_to_integrated(rule)
                    integrated_rules.append(integrated_rule)
                except Exception as e:
                    logger.warning(f"Skipping invalid rule during regeneration: {e}")
                    continue
            
            # Generate timestamp for filenames
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Generate all formats
            await self._generate_complete_ontologies(integrated_rules, timestamp)
            
            # Update cache
            self.last_update = datetime.utcnow()
            
            # Publish event
            await event_bus.publish_event(Event(
                event_type="ontology_regenerated",
                data={
                    "rules_count": len(integrated_rules),
                    "timestamp": timestamp,
                    "regeneration_time": self.last_update.isoformat()
                },
                source="ontology_manager"
            ))
            
            logger.info(f"Complete ontology regeneration completed for {len(integrated_rules)} rules")
            
        except Exception as e:
            logger.error(f"Error regenerating ontologies: {e}")
            raise
    
    async def _update_incremental_ontology(self, integrated_rule: IntegratedRule, old_rule_data: Optional[Dict[str, Any]]) -> None:
        """Update ontology files incrementally."""
        if not RDF_AVAILABLE:
            logger.warning("Cannot perform incremental ontology update - RDFLib not available")
            return
        
        try:
            # Load existing ontology or create new one
            graph = await self._load_or_create_ontology_graph()
            
            # Remove old rule if it exists
            if old_rule_data:
                await self._remove_rule_from_graph(graph, old_rule_data.get('id'))
            
            # Add new/updated rule to graph
            await self._add_rule_to_graph(graph, integrated_rule)
            
            # Save updated graph
            await self._save_ontology_graph(graph, "incremental")
            
        except Exception as e:
            logger.error(f"Error in incremental ontology update: {e}")
            raise
    
    async def _remove_rule_from_ontology(self, rule_id: str) -> None:
        """Remove a specific rule from ontology files."""
        if not RDF_AVAILABLE:
            logger.warning("Cannot remove rule from ontology - RDFLib not available")
            return
        
        try:
            # Load existing ontology
            graph = await self._load_or_create_ontology_graph()
            
            # Remove rule from graph
            await self._remove_rule_from_graph(graph, rule_id)
            
            # Save updated graph
            await self._save_ontology_graph(graph, "incremental")
            
        except Exception as e:
            logger.error(f"Error removing rule from ontology: {e}")
            raise
    
    async def _generate_complete_ontologies(self, integrated_rules: List[IntegratedRule], timestamp: str) -> None:
        """Generate complete ontology files in all formats."""
        try:
            # Generate TTL format
            if RDF_AVAILABLE:
                ttl_content = await self._generate_ttl_ontology(integrated_rules)
                ttl_file = self.output_path / f"integrated_dpv_odrl_odre_{timestamp}.ttl"
                with open(ttl_file, 'w', encoding='utf-8') as f:
                    f.write(ttl_content)
                logger.info(f"Generated TTL ontology: {ttl_file}")
            
            # Generate JSON-LD format
            jsonld_content = await self._generate_jsonld_ontology(integrated_rules)
            jsonld_file = self.output_path / f"integrated_dpv_odrl_odre_{timestamp}.jsonld"
            with open(jsonld_file, 'w', encoding='utf-8') as f:
                json.dump(jsonld_content, f, indent=2, ensure_ascii=False)
            logger.info(f"Generated JSON-LD ontology: {jsonld_file}")
            
            # Generate integrated JSON format
            json_content = [rule.model_dump() for rule in integrated_rules]
            json_file = self.output_path / f"integrated_standards_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, default=str, ensure_ascii=False)
            logger.info(f"Generated JSON ontology: {json_file}")
            
        except Exception as e:
            logger.error(f"Error generating complete ontologies: {e}")
            raise
    
    async def _load_or_create_ontology_graph(self) -> 'Graph':
        """Load existing ontology graph or create a new one."""
        if not RDF_AVAILABLE:
            raise RuntimeError("RDFLib not available for graph operations")
        
        graph = Graph()
        
        # Define namespaces
        DPV = Namespace(Config.DPV_NAMESPACE)
        ODRL = Namespace(Config.ODRL_NAMESPACE)
        ODRE = Namespace(Config.ODRE_NAMESPACE)
        
        # Bind namespaces
        graph.bind("dpv", DPV)
        graph.bind("odrl", ODRL)
        graph.bind("odre", ODRE)
        graph.bind("rdf", RDF)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)
        
        # Try to load existing ontology
        incremental_file = self.output_path / "current_ontology.ttl"
        if incremental_file.exists():
            try:
                graph.parse(str(incremental_file), format='turtle')
                logger.debug("Loaded existing ontology graph")
            except Exception as e:
                logger.warning(f"Could not load existing ontology, creating new: {e}")
        
        return graph
    
    async def _add_rule_to_graph(self, graph: 'Graph', integrated_rule: IntegratedRule) -> None:
        """Add an integrated rule to the RDF graph."""
        if not RDF_AVAILABLE:
            return
        
        # Get namespaces
        DPV = Namespace(Config.DPV_NAMESPACE)
        ODRL = Namespace(Config.ODRL_NAMESPACE)
        ODRE = Namespace(Config.ODRE_NAMESPACE)
        
        # Create URI for the rule
        rule_id_safe = self._safe_uri_encode(integrated_rule.id)
        rule_uri = URIRef(f"urn:rule:{rule_id_safe}")
        
        # Add core types
        graph.add((rule_uri, RDF.type, ODRE.EnforceablePolicy))
        graph.add((rule_uri, RDF.type, DPV.ProcessingActivity))
        graph.add((rule_uri, RDFS.label, Literal(integrated_rule.source_article)))
        
        # Add ODRE properties
        graph.add((rule_uri, ODRE.enforceable, Literal(integrated_rule.odre_enforceable, datatype=XSD.boolean)))
        graph.add((rule_uri, ODRE.enforcement_mode, Literal(integrated_rule.odre_enforcement_mode)))
        graph.add((rule_uri, ODRE.monitoring_required, Literal(integrated_rule.odre_monitoring_required, datatype=XSD.boolean)))
        
        # Add DPV properties
        for processing in integrated_rule.dpv_hasProcessing:
            processing_uri = URIRef(processing)
            graph.add((rule_uri, DPV.hasProcessing, processing_uri))
        
        for purpose in integrated_rule.dpv_hasPurpose:
            purpose_uri = URIRef(purpose)
            graph.add((rule_uri, DPV.hasPurpose, purpose_uri))
        
        for data in integrated_rule.dpv_hasPersonalData:
            data_uri = URIRef(data)
            graph.add((rule_uri, DPV.hasPersonalData, data_uri))
        
        # Add locations with proper encoding
        for location in integrated_rule.dpv_hasLocation:
            if location.startswith("dpv:Country_"):
                country_part = location.replace("dpv:Country_", "")
                encoded_country = self._safe_uri_encode(country_part)
                location_uri = URIRef(f"{Config.DPV_NAMESPACE}Country_{encoded_country}")
            else:
                location_uri = URIRef(location)
            graph.add((rule_uri, DPV.hasLocation, location_uri))
        
        # Add metadata
        graph.add((rule_uri, DPV.hasConfidenceScore, Literal(integrated_rule.confidence_score, datatype=XSD.float)))
        graph.add((rule_uri, DPV.extractedAt, Literal(integrated_rule.extracted_at.isoformat(), datatype=XSD.dateTime)))
        graph.add((rule_uri, DPV.sourceLegislation, Literal(integrated_rule.source_legislation)))
    
    async def _remove_rule_from_graph(self, graph: 'Graph', rule_id: str) -> None:
        """Remove a rule from the RDF graph."""
        if not RDF_AVAILABLE:
            return
        
        rule_id_safe = self._safe_uri_encode(rule_id)
        rule_uri = URIRef(f"urn:rule:{rule_id_safe}")
        
        # Remove all triples where this rule is the subject
        triples_to_remove = list(graph.triples((rule_uri, None, None)))
        for triple in triples_to_remove:
            graph.remove(triple)
        
        logger.debug(f"Removed {len(triples_to_remove)} triples for rule: {rule_id}")
    
    async def _save_ontology_graph(self, graph: 'Graph', file_type: str = "incremental") -> None:
        """Save the ontology graph to file."""
        if not RDF_AVAILABLE:
            return
        
        if file_type == "incremental":
            output_file = self.output_path / "current_ontology.ttl"
        else:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_path / f"ontology_{timestamp}.ttl"
        
        # Serialize to Turtle format
        turtle_content = graph.serialize(format='turtle')
        if isinstance(turtle_content, bytes):
            turtle_content = turtle_content.decode('utf-8')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(turtle_content)
        
        logger.debug(f"Saved ontology graph to: {output_file}")
    
    async def _generate_ttl_ontology(self, integrated_rules: List[IntegratedRule]) -> str:
        """Generate TTL ontology from integrated rules."""
        if not RDF_AVAILABLE:
            return "# RDFLib not available for TTL generation"
        
        graph = Graph()
        
        # Define and bind namespaces
        DPV = Namespace(Config.DPV_NAMESPACE)
        ODRL = Namespace(Config.ODRL_NAMESPACE)
        ODRE = Namespace(Config.ODRE_NAMESPACE)
        
        graph.bind("dpv", DPV)
        graph.bind("odrl", ODRL)
        graph.bind("odre", ODRE)
        graph.bind("rdf", RDF)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)
        
        # Add all rules to graph
        for rule in integrated_rules:
            await self._add_rule_to_graph(graph, rule)
        
        # Serialize to Turtle
        turtle_output = graph.serialize(format='turtle')
        if isinstance(turtle_output, bytes):
            return turtle_output.decode('utf-8')
        return turtle_output
    
    async def _generate_jsonld_ontology(self, integrated_rules: List[IntegratedRule]) -> Dict[str, Any]:
        """Generate JSON-LD ontology from integrated rules."""
        context = {
            "@context": {
                "dpv": Config.DPV_NAMESPACE,
                "odrl": Config.ODRL_NAMESPACE,
                "odre": Config.ODRE_NAMESPACE,
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            }
        }
        
        graph = []
        for rule in integrated_rules:
            rule_id_safe = self._safe_uri_encode(rule.id)
            
            rule_jsonld = {
                "@id": f"urn:rule:{rule_id_safe}",
                "@type": ["odre:EnforceablePolicy", "dpv:ProcessingActivity"],
                "rdfs:label": rule.source_article,
                
                # ODRE Properties
                "odre:enforceable": rule.odre_enforceable,
                "odre:enforcement_mode": rule.odre_enforcement_mode,
                "odre:monitoring_required": rule.odre_monitoring_required,
                
                # DPV Properties
                "dpv:hasProcessing": [{"@id": uri} for uri in rule.dpv_hasProcessing],
                "dpv:hasPurpose": [{"@id": uri} for uri in rule.dpv_hasPurpose],
                "dpv:hasPersonalData": [{"@id": uri} for uri in rule.dpv_hasPersonalData],
                
                # Locations with proper encoding
                "dpv:hasLocation": [
                    {
                        "@id": (
                            f"{Config.DPV_NAMESPACE}Country_{self._safe_uri_encode(uri.replace('dpv:Country_', ''))}" 
                            if uri.startswith("dpv:Country_") else uri
                        )
                    } 
                    for uri in rule.dpv_hasLocation
                ],
                
                # Metadata
                "dpv:hasConfidenceScore": {
                    "@value": rule.confidence_score,
                    "@type": "xsd:float"
                },
                "dpv:extractedAt": {
                    "@value": rule.extracted_at.isoformat(),
                    "@type": "xsd:dateTime"
                },
                "dpv:sourceLegislation": rule.source_legislation
            }
            
            # Add optional properties
            if rule.dpv_hasDataController:
                rule_jsonld["dpv:hasDataController"] = {"@id": rule.dpv_hasDataController}
            if rule.dpv_hasDataProcessor:
                rule_jsonld["dpv:hasDataProcessor"] = {"@id": rule.dpv_hasDataProcessor}
            
            graph.append(rule_jsonld)
        
        return {**context, "@graph": graph}
    
    def get_ontology_status(self) -> Dict[str, Any]:
        """Get current ontology status."""
        status = {
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "rdf_available": RDF_AVAILABLE,
            "output_path": str(self.output_path),
            "files": []
        }
        
        # List generated files
        if self.output_path.exists():
            for file in self.output_path.glob("*.ttl"):
                status["files"].append({
                    "name": file.name,
                    "type": "turtle",
                    "size": file.stat().st_size,
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
            
            for file in self.output_path.glob("*.jsonld"):
                status["files"].append({
                    "name": file.name,
                    "type": "json-ld",
                    "size": file.stat().st_size,
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
        
        return status
    
    async def validate_ontology(self, file_path: Path) -> Dict[str, Any]:
        """Validate an ontology file."""
        validation_result = {
            "valid": False,
            "format": None,
            "triples_count": 0,
            "errors": []
        }
        
        if not RDF_AVAILABLE:
            validation_result["errors"].append("RDFLib not available for validation")
            return validation_result
        
        try:
            graph = Graph()
            
            # Detect and parse format
            if file_path.suffix == '.ttl':
                graph.parse(str(file_path), format='turtle')
                validation_result["format"] = "turtle"
            elif file_path.suffix == '.jsonld':
                graph.parse(str(file_path), format='json-ld')
                validation_result["format"] = "json-ld"
            else:
                validation_result["errors"].append(f"Unsupported format: {file_path.suffix}")
                return validation_result
            
            validation_result["triples_count"] = len(graph)
            validation_result["valid"] = True
            
        except Exception as e:
            validation_result["errors"].append(str(e))
        
        return validation_result