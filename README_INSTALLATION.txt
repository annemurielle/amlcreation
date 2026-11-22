INSTALLATION, CORRECTIF SEO SANS CHANGEMENT DES URL DE CONFIDENTIALITE

1. Copier le ZIP dans Téléchargements.
2. Dans le Terminal, depuis le dépôt Git local :

cd "/Users/largeram/_amlCreationGitHub/amlcreation" && ditto -x -k "$HOME/Downloads/AML_Creation_Audit_SEO_AppStore_Safe_2026-11-19.zip" . && git diff --check && git status --short

3. Ouvrir et vérifier : Somnifox/marketing_en.html, ZenCircle/marketing_en.html, MahjongCastle/marketing_en.html.
4. Ne publier qu'après vérification visuelle. L'archive NE remplace pas les dossiers complets.
5. Ne modifier aucun champ dans App Store Connect avant d'avoir vérifié les URLs actuellement configurées.

IMPORTANT : App Store Connect est privé et ses champs Support URL, Marketing URL et Privacy URL
ne peuvent pas être lus directement à partir du dépôt. Le rapport indique seulement ce qui est
visible sur les fiches publiques et les ressources présentes localement.

Changements : 42 pages HTML existantes ont reçu des balises SEO (canonical, hreflang, ou image de
partage absolue) ; 2 alias de confidentialité Unicode ont été ajoutés ; rapport inclus.
Aucun lien existant, CSS, JS, fichier de workflow, sitemap ou texte juridique n'a été supprimé.
