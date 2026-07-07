import argparse
import asyncio
import logging
import shutil
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Asynchronously sort files from source folder into output "
            "subfolders based on file extensions."
        )
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to the source folder with files to sort",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the output folder where sorted files will be copied",
    )
    return parser.parse_args()


def validate_paths(source: Path, output: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")

    if not source.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {source}")

    if output.exists() and not output.is_dir():
        raise NotADirectoryError(f"Output path is not a folder: {output}")


def get_extension_folder(file_path: Path) -> str:
    suffix = file_path.suffix.lower().lstrip(".")
    return suffix if suffix else "no_extension"


def get_unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination

    counter = 1
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent

    while True:
        new_destination = parent / f"{stem}_{counter}{suffix}"
        if not new_destination.exists():
            return new_destination
        counter += 1


async def copy_file(file_path: Path, output_folder: Path) -> None:
    try:
        extension_folder = get_extension_folder(file_path)
        destination_folder = output_folder / extension_folder

        await asyncio.to_thread(destination_folder.mkdir, parents=True, exist_ok=True)

        destination = get_unique_destination(destination_folder / file_path.name)
        await asyncio.to_thread(shutil.copy2, file_path, destination)

        logger.info("Copied %s -> %s", file_path, destination)
    except Exception as error:
        logger.error("Error copying file %s: %s", file_path, error)


async def read_folder(source_folder: Path, output_folder: Path) -> None:
    tasks = []

    try:
        for item in source_folder.iterdir():
            if item.is_dir():
                tasks.append(read_folder(item, output_folder))
            elif item.is_file():
                tasks.append(copy_file(item, output_folder))
    except Exception as error:
        logger.error("Error reading folder %s: %s", source_folder, error)
        return

    if tasks:
        await asyncio.gather(*tasks)


async def main() -> None:
    args = parse_arguments()
    source_folder = args.source.resolve()
    output_folder = args.output.resolve()

    try:
        validate_paths(source_folder, output_folder)
        await asyncio.to_thread(output_folder.mkdir, parents=True, exist_ok=True)
        await read_folder(source_folder, output_folder)
        logger.info("Sorting completed successfully")
    except Exception as error:
        logger.error("Program finished with error: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    asyncio.run(main())
