"""
Turn them tables into plots
"""
import os
import matplotlib
matplotlib.use('Agg')
from .utils import read_binned_df, weighting_vars, decipher_filename
from .plotting import plot_all
import logging


logger = logging.getLogger("fast_plotter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def arg_parser(args=None):
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("tables", type=str, nargs="+",
                        help="Table files to process")
    parser.add_argument("-o", "--outdir", type=str, default="plots",
                        help="Output directory to save plots to")
    parser.add_argument("-e", "--extension", type=str, default="png",
                        help="File extension for images")
    parser.add_argument("-w", "--weights", default=[], type=lambda x: x.split(","),
                        help="comma-separated list of weight schemes to plot things for")
    parser.add_argument("-d", "--data", default="data",
                        help="Regular expression to identify real data datasets from their name")
    parser.add_argument("-s", "--signal", default="signal",
                        help="Regular expression to identify signal MC datasets from their name")
    parser.add_argument("--dataset-col", default="dataset",
                        help="Name of column to be used to define multiple-lines for 1D plots")
    parser.add_argument("-l", "--lumi", default=None, type=float,
                        help="Scale the MC yields by this lumi")
    parser.add_argument("-y", "--yscale", default="log", choices=["log", "linear"],
                        help="Use this scale for the y-axis")
    return parser


def main(args=None):
    if args is None:
        args = arg_parser().parse_args()

    for infile in args.tables:
        process_one_file(infile, args)


def process_one_file(infile, args):
    logger.info("Processing: " + infile)
    df = read_binned_df(infile)
    weights = weighting_vars(df)
    for weight in weights:
        if args.weights and weight not in args.weights:
            continue
        if weight == "n":
            df_filtered = df.filter(weight, axis="columns").copy()
            df_filtered.rename({weight: "sumw"}, axis="columns", inplace=True)
            df_filtered["sumw2"] = df_filtered.sumw
        else:
            df_filtered = df.filter(like=weight, axis="columns").copy()
            if "n" in df.columns:
                isnull = df_filtered.isnull()
                for col in df_filtered.columns:
                    df_filtered[col][isnull[col]] = df["n"][isnull[col]]
            df_filtered.columns = [n.replace(weight + ":", "") for n in df_filtered.columns]
        plots = plot_all(df_filtered, infile + "__" + weight, dataset_col=args.dataset_col,
                         data=args.data, signal=args.signal, scale_sims=args.lumi, yscale=args.yscale)
        save_plots(infile, weight, plots, args.outdir, args.extension)


def save_plots(infile, weight, plots, outdir, extension):
    binning, _ = decipher_filename(infile)
    kernel = "plot_" + ".".join(binning)
    kernel += "--" + weight
    kernel = os.path.join(outdir, kernel)
    for properties, plot in plots.items():
        insert = "-".join("%s_%s" % prop for prop in properties)
        path = kernel + "--" + insert
        path += "." + extension
        logger.info("Saving plot: " + path)
        plot.savefig(path)
        matplotlib.pyplot.close(plot)


if __name__ == "__main__":
    args = arg_parser().parse_args()
    main(args)
