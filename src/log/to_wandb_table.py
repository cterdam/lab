import datetime

import wandb


def get_wandb_table_logger(logger):

    def to_wandb_table(msg):
        """Sink that accumulates text log entries on a wandb table.

        Only added as a sink to core logger if using wandb.
        """

        curr_time = msg.record["time"].astimezone(datetime.timezone.utc)
        logger.wandb_table_data.append(
            [
                msg.record["file"].path,
                msg.record["line"],
                msg.record["function"],
                msg.record["level"].name,
                curr_time.strftime("%Y-%m-%d"),
                curr_time.strftime("%H:%M:%S"),
                msg.record["message"],
            ]
        )

        table = wandb.Table(
            columns=logger.wandb_table_cols, data=logger.wandb_table_data
        )

        # Each time this actually creates a new table, but old tables also seem updated
        # So in the ened all tables are the same but there are many tables
        logger.wandb_run.log({"logs": table})

    return to_wandb_table
