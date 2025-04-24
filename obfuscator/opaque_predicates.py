import random
import re
import logging


class OpaquePredicateInjector:
    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        return logging.getLogger("OpaquePredicateInjector")

    def inject(self, code: str) -> str:
        """
        Вставляет Opaque Predicates перед if/while/for блоками для запутывания
        """
        self.logger.info("🌀 Внедрение Opaque Predicates...")

        opaque_patterns = [
            "if ((42 * 2 == 84) && (100 > 50)) {}",
            "if ((7 * 7) % 2 == 1 || false) {}",
            "if ((0b101010 & 0b010101) == 0) {}",
            "if ((123 ^ 123) == 0) {}"
        ]

        lines = code.splitlines()
        obf_code = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("if ") or stripped.startswith("while ") or stripped.startswith("for "):
                predicate = random.choice(opaque_patterns)
                indent = re.match(r"\s*", line).group(0)
                obf_code.append(indent + predicate)
            obf_code.append(line)

        self.logger.info("✅ Opaque Predicates вставлены.")
        return "\n".join(obf_code)
