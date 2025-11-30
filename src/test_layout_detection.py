"""
Script de test pour validation de la détection de layout
"""
import sys
from skimage import io
import config
from src.preprocessing import pretraiter_image
from src.analysis import detecter_touches, identifier_zones_cles, classifier_clavier

def tester_image(image_path, expected_layout=None):
    """
    Teste la détection sur une image avec validation optionnelle.
    
    Args:
        image_path: Chemin de l'image
        expected_layout: Layout attendu (ex: "QWERTY_US") pour validation
    
    Returns:
        dict: Résultats détaillés
    """
    print("\n" + "="*70)
    print(f"TEST: {image_path}")
    print("="*70)
    
    try:
        # Chargement
        img = io.imread(image_path)
        print(f"✓ Image chargée: {img.shape}")
        
        # Prétraitement
        img_bin, img_gris = pretraiter_image(img)
        print("✓ Prétraitement OK")
        
        # Détection
        touches, _, _, _ = detecter_touches(img_bin)
        print(f"✓ {len(touches)} touches détectées")
        
        if len(touches) < config.MIN_TOUCHES_DETECTEES:
            return {
                'success': False,
                'error': f"Touches insuffisantes: {len(touches)}",
                'touches_count': len(touches)
            }
        
        # Zoning
        rois = identifier_zones_cles(touches)
        if not rois:
            return {
                'success': False,
                'error': "Échec identification zones",
                'touches_count': len(touches)
            }
        
        zones_ok = sum(1 for k, v in rois.items() if v and k != "h_ref")
        print(f"✓ {zones_ok}/5 zones identifiées")
        
        # Classification
        verdict, debug = classifier_clavier(rois, img_gris, touches)
        
        # Affichage résultats
        print("\n" + "-"*70)
        print("RÉSULTATS:")
        print("-"*70)
        print(f"  Format   : {verdict.get('ISO_ANSI', '?')}")
        print(f"  Système  : {verdict.get('MAC_WIN', '?')}")
        print(f"  Layout   : {verdict.get('LAYOUT', '?')}")
        
        if 'LAYOUT_FULL' in verdict:
            print(f"  Détaillé : {verdict['LAYOUT_FULL']}")
            print(f"  Région   : {verdict.get('LAYOUT_REGION', '?')}")
        
        print(f"\n  Méthode  : {debug.get('Layout_Method', '?')}")
        print(f"  Confiance: {debug.get('Layout_Confidence', 0):.0%}")
        
        if 'Layout_Seq_Row1' in debug:
            print(f"  Seq. R1  : {debug['Layout_Seq_Row1']}")
        if 'Layout_Seq_Row2' in debug:
            print(f"  Seq. R2  : {debug['Layout_Seq_Row2']}")
        
        # Validation
        success = True
        if expected_layout:
            detected = verdict.get('LAYOUT_FULL', verdict.get('LAYOUT', ''))
            match = expected_layout in detected or detected in expected_layout
            
            print(f"\n  Attendu  : {expected_layout}")
            print(f"  Statut   : {'✓ CORRECT' if match else '✗ ERREUR'}")
            success = match
        
        return {
            'success': success,
            'verdict': verdict,
            'debug': debug,
            'touches_count': len(touches),
            'zones_count': zones_ok,
            'expected': expected_layout,
            'match': expected_layout in verdict.get('LAYOUT_FULL', '') if expected_layout else None
        }
        
    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def test_suite():
    """
    Suite de tests avec plusieurs images de référence.
    Adaptez les chemins et layouts attendus selon vos images.
    """
    tests = [
        {
            'path': 'data/inputs/qwerty_us_sample.png',
            'expected': 'QWERTY_US',
            'description': 'Clavier QWERTY US ANSI'
        },
        {
            'path': 'data/inputs/qwerty_uk_sample.png',
            'expected': 'QWERTY_UK',
            'description': 'Clavier QWERTY UK ISO'
        },
        {
            'path': 'data/inputs/qwertz_de_sample.png',
            'expected': 'QWERTZ_DE',
            'description': 'Clavier QWERTZ Allemand'
        },
        {
            'path': 'data/inputs/azerty_fr_sample.png',
            'expected': 'AZERTY_FR',
            'description': 'Clavier AZERTY Français'
        },
        {
            'path': 'data/inputs/azerty_be_sample.png',
            'expected': 'AZERTY_BE',
            'description': 'Clavier AZERTY Belge'
        }
    ]
    
    print("\n" + "="*70)
    print("SUITE DE TESTS - DÉTECTION DE LAYOUT")
    print("="*70)
    
    resultats = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n[Test {i}/{len(tests)}] {test['description']}")
        
        try:
            result = tester_image(test['path'], test.get('expected'))
            resultats.append({
                'test': test['description'],
                'result': result
            })
        except FileNotFoundError:
            print(f"⚠️  Fichier non trouvé: {test['path']}")
            resultats.append({
                'test': test['description'],
                'result': {'success': False, 'error': 'File not found'}
            })
    
    # Rapport final
    print("\n\n" + "="*70)
    print("RAPPORT FINAL")
    print("="*70)
    
    success_count = sum(1 for r in resultats if r['result'].get('success'))
    total = len(resultats)
    
    print(f"\nRésultats: {success_count}/{total} réussis ({success_count/total*100:.0f}%)")
    print("\nDétails:")
    
    for r in resultats:
        status = "✓" if r['result'].get('success') else "✗"
        print(f"  {status} {r['test']}")
        
        if not r['result'].get('success') and 'error' in r['result']:
            print(f"      Erreur: {r['result']['error']}")


def test_image_unique(image_path):
    """Test rapide sur une seule image."""
    result = tester_image(image_path)
    return result['success']


if __name__ == "__main__":
    # Mode CLI
    if len(sys.argv) > 1:
        # Test d'une image spécifique
        image_path = sys.argv[1]
        expected = sys.argv[2] if len(sys.argv) > 2 else None
        tester_image(image_path, expected)
    else:
        # Suite de tests complète
        test_suite()