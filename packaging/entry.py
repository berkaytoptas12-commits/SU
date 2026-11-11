"""PyInstaller entry point for SurecUzmani.exe ("Süreç Uzmanı")."""
import multiprocessing

from techrag.desktop import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
