# -*- coding: utf-8 -*-
import ast
import astor
import logging
import random

class ControlFlowFlattener:
    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        return logging.getLogger("ControlFlowFlattener")

    def transform(self, source_code):
        """Применяет и flattening, и opaque predicates"""
        code = self.flatten_control_flow(source_code)
        code = self.add_opaque_predicates(code)
        return code

    def flatten_control_flow(self, source_code):
        """Control Flow Flattening"""
        self.logger.info("🚀 Начинаем обфускацию потока управления...")
        try:
            tree = ast.parse(source_code)
            new_body = []
            state_counter = 1
            state_var = "state"

            while_loop = ast.parse(f"while {state_var} != -1:\n    pass").body[0]
            new_body.append(ast.parse(f"{state_var} = 0").body[0])
            new_body.append(while_loop)

            state_map = {}
            current_state = 1

            for stmt in tree.body:
                state_map[current_state] = stmt
                current_state += 1

            for state, statement in state_map.items():
                if_state = ast.parse(f"if {state_var} == {state}: pass").body[0]
                if_state.body.pop()
                if_state.body.append(statement)
                next_state = state + 1 if state + 1 in state_map else -1
                next_state_stmt = ast.parse(f"{state_var} = {next_state}").body[0]
                if_state.body.append(next_state_stmt)
                while_loop.body.append(if_state)

            obfuscated_code = astor.to_source(ast.Module(body=new_body))
            self.logger.info("✅ Обфускация потока управления завершена.")
            return obfuscated_code
        except Exception as e:
            self.logger.error(f"❌ Ошибка обфускации: {e}")
            return source_code

    def add_opaque_predicates(self, source_code):
        """Вставка Opaque Predicates"""
        self.logger.info("🚀 Добавляем Opaque Predicates...")
        try:
            tree = ast.parse(source_code)
            new_body = []

            for stmt in tree.body:
                opaque_conditions = [
                    "42 * 2 == 84 and 48 > 0",
                    "(100 - 50) * 2 == 100",
                    "(7 * 7) % 2 == 1",
                    "(x ^ x) == 0",
                    "0b101010 & 0b010101 == 0"
                ]
                opaque_condition = random.choice(opaque_conditions)

                dead_code_variants = [
                    "if False:\n    print('Этот код никогда не выполнится')",
                    "if (7 * 7) % 2 == 0 and (3 + 3) < 0:\n    print('Недостижимый код')",
                    "if 100 < 50:\n    print('Невозможный вывод')"
                ]
                dead_ast = ast.parse(random.choice(dead_code_variants)).body[0]

                opaque_if = ast.parse(f"if {opaque_condition}:\n    pass").body[0]
                opaque_if.body.pop()
                opaque_if.body.append(stmt)
                new_body.append(opaque_if)
                new_body.append(dead_ast)

            obfuscated_code = astor.to_source(ast.Module(body=new_body))
            self.logger.info("✅ Opaque Predicates добавлены.")
            return obfuscated_code
        except Exception as e:
            self.logger.error(f"❌ Ошибка добавления Opaque Predicates: {e}")
            return source_code
