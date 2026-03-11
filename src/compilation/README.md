## Compilation

Pipeline de compilation des sources en binaires ELF pour l'analyse par angr.

### Objectif

Compiler chaque fichier source (C, C++, Rust, Go) en binaire avec symboles de
debug (DWARF) selon une matrice *architecture × niveau d'optimisation*.
Les binaires sont nommés `.exe` pour faciliter leur traitement dans la pipeline
de désassemblage (angr).

### Langages & compilateurs

| Langage | Compilateur         | Cross-compilation              |
|---------|---------------------|--------------------------------|
| C       | `gcc`               | `gcc-multilib`, `gcc-arm-linux-gnueabihf`, `gcc-aarch64-linux-gnu` |
| C++     | `g++`               | idem C                         |
| Rust    | `rustc`             | via `rustup target add <triple>` |
| Go      | `go build`          | natif via `GOARCH`/`GOOS`      |

### Architectures cibles

| Identifiant | Description            |
|-------------|------------------------|
| `x86`       | 32-bit Intel/AMD       |
| `x86_64`    | 64-bit Intel/AMD       |
| `arm`       | ARMv7 32-bit (HF)      |
| `aarch64`   | ARM 64-bit             |

### Niveaux d'optimisation

- **C/C++** : O0, O1, O2, O3, Os
- **Rust**  : O0, O1, O2, O3
- **Go**    : O0 (no-opt/no-inline), O2 (défaut Go)

Tous les binaires incluent les symboles de debug complets (`-g` / `debuginfo=2`).

### Structure de sortie

```
output/binaries/
  <source>/<task>/<lang>/
    <arch>/
      <opt>/
        impl_01.exe
        impl_02.exe
```

Exemple :
```
output/binaries/rosetta_code/100_doors/C/x86_64/O2/impl_01.exe
output/binaries/rosetta_code/100_doors/Rust/arm/O0/impl_01.exe
```

### Utilisation

```bash
# Compiler tout le dataset sample (toutes archs, tous niveaux)
python src/compilation/compile_pipeline.py -i data/sample -o output/binaries

# Compilation rapide : x86_64 uniquement, O0 et O2
python src/compilation/compile_pipeline.py -i data/sample -o output/binaries \
    --arch x86_64 --opt O0 O2

# Sur un sous-dossier spécifique
python src/compilation/compile_pipeline.py \
    -i data/sample/rosetta_code/100_doors \
    -o output/test
```

Un fichier `compile.log` est créé dans le dossier de sortie avec le détail
complet (succès, échecs + message d'erreur du compilateur).

### Prérequis

```bash
# Debian/Ubuntu — cross-compilateurs C/C++
sudo apt install gcc-multilib g++-multilib \
    gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf \
    gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# Rust — targets cross-compilation
rustup target add i686-unknown-linux-gnu
rustup target add armv7-unknown-linux-gnueabihf
rustup target add aarch64-unknown-linux-gnu

# Go — pas de dépendance supplémentaire (cross-compilation natif)
```

Si un compilateur est absent, la combinaison est ignorée (warning dans les logs)
et le reste de la compilation continue.

### Suite du pipeline

Les binaires `.exe` (ELF + DWARF) sont prêts pour :
- Désassemblage et analyse avec **angr**
- Extraction de features pour la détection de similarité binaire (BCSD)
