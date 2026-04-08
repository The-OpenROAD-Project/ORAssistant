import json
import scipy

from src.openroad_mcp.server.orfs.orfs_tools import ORFS

class ORFSOptimizer(ORFS):
    @staticmethod
    @ORFS.mcp.tool
    def calc_cost() -> str:
        """
        Calculate cost function
        """
        result_list = []

        param_keys = ["CORE_UTILIZATION"]
        BOUNDS = [(0.01, 0.99)]
        PARAMS = [0.05]

        def evaluate(target):
            # Force step increments of at least 0.01
            x = [max(BOUNDS[i][0], min(BOUNDS[i][1], round(target[i]/0.01)*0.01)) for i in range(len(target))]

            modify = {param_keys[0]: x[0]*100}
            ORFS.server.orfs_env.update(modify)

            # Run flow
            ORFS.server._create_dynamic_makefile()
            ORFS.server._make("clean_floorplan")
            ORFS.server._make("floorplan")
            ORFS.server._make("update_metadata")

            # Read metric
            with open(f"{ORFS.server.flow_dir}/designs/{ORFS.server.platform}/{ORFS.server.design}/metadata-base-ok.json", 'r') as f:
                metrics = json.load(f)

            # Floorplan die area as cost
            cost = metrics["floorplan__design__die__area"]
            result_list.append(x[0]*100)
            return cost

        def report(xk):
            print("Current params:", xk)

        ORFS.server.opt_method = "Powell"
        ORFS.server.logging(f"Running {ORFS.server.opt_method} optimizer...")

        result = scipy.optimize.minimize(
            evaluate,
            PARAMS,
            bounds=BOUNDS,
            method=ORFS.server.opt_method,
            options={
                "maxiter": 1000,
                "xtol": 0.01,  # minimum change in x before stopping
                "ftol": 0.0,   # don't stop due to small cost change
                "disp": True,
            },
            callback=report
        )

        ORFS.server.logging(result)
        ORFS.server.logging(result_list)

        return ""
