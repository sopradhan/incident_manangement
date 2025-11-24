import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from incident_iq.gen_ai.services import CorrectiveActionGenerator
from incident_iq.config.env_config import EnvConfig


def main():
    parser = argparse.ArgumentParser(
        description="Corrective Action Generator - RAG-based action generation from classified incidents"
    )
    
    parser.add_argument(
        '--action',
        choices=['ingest', 'process', 'batch', 'auto'],
        default='process',
        help='Action to perform'
    )
    
    parser.add_argument(
        '--classifier-id',
        type=int,
        help='Single classifier_output ID to process'
    )
    
    parser.add_argument(
        '--classifier-ids',
        type=str,
        help='Comma-separated list of classifier_output IDs'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Limit for auto processing (default: 10)'
    )
    
    parser.add_argument(
        '--user-id',
        type=str,
        default='system',
        help='User ID for RBAC context'
    )
    
    parser.add_argument(
        '--config-dir',
        type=str,
        default=None,
        help='RAG config directory (default: from .env)'
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    db_path = EnvConfig.get_db_path()
    config_dir = args.config_dir or EnvConfig.get_rag_config_path()
    
    print(f"\n{'='*70}")
    print(f"CORRECTIVE ACTION GENERATOR - RAG-based Generation")
    print(f"{'='*70}")
    print(f"Database: {db_path}")
    print(f"Config: {config_dir}")
    print(f"Action: {args.action}")
    print(f"{'='*70}\n")
    
    try:
        with CorrectiveActionGenerator(db_path, config_dir) as generator:
            
            if args.action == 'ingest':
                # Ingest knowledge base
                result = generator.ingest_knowledge_base()
                print(f"\nIngestion Result:")
                print(json.dumps(result, indent=2))
            
            elif args.action == 'process':
                # Process single classifier output
                if not args.classifier_id:
                    print("ERROR: --classifier-id required for 'process' action")
                    return 1
                
                result = generator.process_classifier_output(args.classifier_id, args.user_id)
                
                if result.get('success'):
                    generator.save_corrective_action(
                        args.classifier_id,
                        result.get('corrective_action', ''),
                        result
                    )
                
                print(f"\nProcessing Result:")
                print(json.dumps(result, indent=2, default=str))
            
            elif args.action == 'batch':
                # Process batch
                if not args.classifier_ids:
                    print("ERROR: --classifier-ids required for 'batch' action")
                    return 1
                
                classifier_ids = [int(cid.strip()) for cid in args.classifier_ids.split(',')]
                results = generator.process_batch(classifier_ids, args.user_id, save_results=True)
                
                print(f"\nBatch Processing Results:")
                print(json.dumps(results, indent=2, default=str))
                
                # Summary
                successful = sum(1 for r in results if r.get('success'))
                print(f"\nSummary: {successful}/{len(results)} successful")
            
            elif args.action == 'auto':
                # Auto-process unprocessed classifier outputs
                results = generator.process_unprocessed(limit=args.limit, user_id=args.user_id)
                
                if results:
                    print(f"\nAuto-Processing Results:")
                    print(json.dumps(results, indent=2, default=str))
                    
                    # Summary
                    successful = sum(1 for r in results if r.get('success'))
                    print(f"\nSummary: {successful}/{len(results)} successful")
                else:
                    print("No incidents to process")
        
        print(f"\n{'='*70}")
        print("Pipeline completed successfully")
        print(f"{'='*70}\n")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
