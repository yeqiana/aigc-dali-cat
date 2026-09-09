class MigrationRepository:
    """Repository迁移阶段状态记录。"""

    def __init__(self):
        self.enabled = True

    def should_write_secondary(self) -> bool:
        return self.enabled

    def enable_secondary_write(self):
        self.enabled = True

    def disable_secondary_write(self):
        self.enabled = False
