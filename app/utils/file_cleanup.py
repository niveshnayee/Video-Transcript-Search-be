import os

class FileCleanup:
    @staticmethod
    def cleanup_temp_files(file_paths):
        """
        Delete temporary files to free up space.
        """
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)


