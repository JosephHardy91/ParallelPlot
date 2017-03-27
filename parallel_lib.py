__author__ = 'joe'
from collections import defaultdict
import random
import matplotlib.pyplot as plt



class ParallelPlot(object):
    def __init__(self, plot_dictionary):
        '''Plot dictionary is a series of keys with lists of possible values'''
        self.plot_dictionary = plot_dictionary
        self.cols = []
        self.dummies = 0

    def add_col(self, rows):
        self.cols.append([None for _ in range(rows)])

    def add_bar(self, col, row, bar_type='dummy', bar_values=None):
        '''bar_values is a string to access self.plot_dictionary
            rows are drawn from the bottom up, i.e. bar at row 1 will be higher than bar at row 0'''
        # dummy,discrete, or continuous
        if len(self.cols) < col - 1:
            raise "Must add column %d first." % col
        if len(self.cols[col]) < row:
            raise "Row %d is outside column row number %d." % (row, len(self.cols[col]))
        if bar_values is None and bar_type != 'dummy':
            raise "Must have values for any non-dummy bar."
        if bar_type == 'dummy':
            self.dummies += 1
            self.cols[col][row] = DummyBar(self.dummies)
        elif bar_type == 'discrete':
            self.cols[col][row] = DiscreteBar(bar_values, self.plot_dictionary[bar_values])
        elif bar_type == 'continuous':
            self.cols[col][row] = ContinuousBar(bar_values, self.plot_dictionary[bar_values])  # min and max
        else:
            raise "Unrecognized bar type."

    def link(self, link_dictionary):
        '''link dictionary is a dictionary of one-valued(string or number)
         instances by the same keys in plot_dictionary'''
        for col_n, col in enumerate(self.cols[:-1]):
            for row in col:
                for row2 in self.cols[col_n + 1]:
                    row.link_to(row2, link_dictionary)

    def draw(self, output_file, row_pad=0.05, col_pad=0.05):
        fig, ax = plt.subplots()
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.0])
        column_size = (1 - (len(self.cols) + 1) * col_pad) / len(self.cols)
        for col_n, col in enumerate(self.cols):
            x_loc = (col_pad * (col_n + 1)) + (column_size / 2.) + column_size * col_n
            row_size = (1 - (len(col) + 1) * row_pad) / len(col)
            for row_n, row in enumerate(col):
                y_loc = (row_pad * (row_n + 1)) + (row_size / 2.) + row_size * row_n
                y_min = y_loc - (row_size / 2.)
                y_max = y_loc + (row_size / 2.)
                row.set_plot_info((x_loc, (y_loc, y_min, y_max)))

        for col_n, col in enumerate(self.cols[:-1]):
            for row_n, row in enumerate(col):
                row.draw(ax)

        for row in self.cols[-1]:
            ax.axvline(row.x_loc, row.y_min, row.y_max, c='black')
            row.draw_labels(ax)
        plt.savefig(output_file)
        plt.show()


class DummyBar(object):
    def __init__(self, dummy_num):
        self.name = 'Dummy %d' % dummy_num
        self.link_to_bars = defaultdict(list)
        self.link_to_values = defaultdict(list)

    def __repr__(self):
        if len(self.link_to_bars) > 0:
            return 'Dummy Bar Linked to %s' % ','.join(self.link_to_bars)
        return 'Dummy Bar'

    def link_to(self, link_to_bar, value_dictionary):
        self.link_to_bars[link_to_bar.name] = link_to_bar
        if isinstance(link_to_bar, DummyBar):
            self.link_to_values[link_to_bar.name] = [((0.5, 0.5), 'black')
                                                     for _ in range(value_dictionary[link_to_bar.name])]
        elif isinstance(link_to_bar, DiscreteBar):
            self.link_to_values[link_to_bar.name] = [((0.5, link_to_bar.values[dis_val]), 'black')
                                                     for dis_val in value_dictionary[link_to_bar.name]]
        elif isinstance(link_to_bar, ContinuousBar):
            self.link_to_values[link_to_bar.name] = [
                ((0.5, link_to_bar.norm_value(con_val)), 'black') for con_val in
                value_dictionary[link_to_bar.name]]

    def set_plot_info(self, coord_tup):
        self.x_loc, (self.y_loc, self.y_min, self.y_max) = coord_tup

    def val_to_y_loc(self, val):
        return self.y_min + (self.y_max - self.y_min) * val

    def draw(self, surface):
        surface.axvline(self.x_loc, self.y_min, self.y_max, c='black')
        self.draw_labels(surface)
        for linked_bar in self.link_to_values:
            for y_val_pair in self.link_to_values[linked_bar]:
                (this_y, link_y), color = y_val_pair
                this_y = self.val_to_y_loc(this_y)
                link_y = self.link_to_bars[linked_bar].val_to_y_loc(link_y)
                surface.plot((self.x_loc, self.link_to_bars[linked_bar].x_loc), (this_y, link_y), c=color)

    def draw_labels(self, surface):
        pass


class DiscreteBar(object):
    def __init__(self, name, values):
        self.name = name
        self.link_to_bars = defaultdict(list)
        self.link_to_values = defaultdict(list)
        self.values = {value: (1. / (len(values) + 1)) * (i + 1)
                       for i, value in enumerate(values)}
        self.color_values = {
            value: (random.random() for _ in range(3)) for vi, value in
            enumerate(self.values)}

    def __repr__(self):
        if len(self.link_to_bars) > 0:
            return 'Discrete Bar <%s> Linked to %s' % (self.name, ','.join(self.link_to_bars))
        return 'Discrete Bar <%s>' % self.name

    def link_to(self, link_to_bar, value_dictionary):
        self.link_to_bars[link_to_bar.name] = link_to_bar
        if isinstance(link_to_bar, DummyBar):
            self.link_to_values[link_to_bar.name] = [((self.values[dis_val], 0.5), self.color_values[dis_val])
                                                     for dis_val in value_dictionary[self.name]]
        elif isinstance(link_to_bar, DiscreteBar):
            self.link_to_values[link_to_bar.name] = [((self.values[dis_val1], link_to_bar.values[dis_val2]),
                                                      self.color_values[dis_val1])
                                                     for dis_val1, dis_val2 in
                                                     zip(value_dictionary[self.name],
                                                         value_dictionary[link_to_bar.name])]
        elif isinstance(link_to_bar, ContinuousBar):
            self.link_to_values[link_to_bar.name] = [
                ((self.values[dis_val], link_to_bar.norm_value(con_val)),
                 self.color_values[dis_val])
                for dis_val, con_val in
                zip(value_dictionary[self.name], value_dictionary[link_to_bar.name])]

    def set_plot_info(self, coord_tup):
        self.x_loc, (self.y_loc, self.y_min, self.y_max) = coord_tup

    def val_to_y_loc(self, val):
        return self.y_min + (self.y_max - self.y_min) * val

    def draw(self, surface):
        surface.axvline(self.x_loc, self.y_min, self.y_max, c='black')
        self.draw_labels(surface)
        for linked_bar in self.link_to_values:
            for y_val_pair in self.link_to_values[linked_bar]:
                (this_y, link_y), color = y_val_pair
                this_y = self.val_to_y_loc(this_y)
                link_y = self.link_to_bars[linked_bar].val_to_y_loc(link_y)
                surface.plot((self.x_loc, self.link_to_bars[linked_bar].x_loc), (this_y, link_y), c=color)

    def draw_labels(self, surface):
        surface.text(self.x_loc * (.975 + 1) / 2, self.y_max + 0.035, self.name, fontsize=10)
        for val in self.values:
            surface.text(self.x_loc, self.val_to_y_loc(self.values[val]), val, fontsize=10)


class ContinuousBar(object):
    def __init__(self, name, values):
        self.name = name
        self.link_to_bars = defaultdict(list)
        self.link_to_values = defaultdict(list)
        self.min_value = float(values[0])
        self.max_value = float(values[1])

    def __repr__(self):
        if len(self.link_to_bars) > 0:
            return 'Continuous Bar <%s> Linked to %s' % (self.name, ','.join(self.link_to_bars))
        return 'Continuous Bar <%s>' % self.name

    def link_to(self, link_to_bar, value_dictionary):
        self.link_to_bars[link_to_bar.name] = link_to_bar
        if isinstance(link_to_bar, DummyBar):
            self.link_to_values[link_to_bar.name] = [((self.norm_value(con_val), 0.5), str(self.norm_value(con_val)))
                                                     for con_val in value_dictionary[self.name]]
        elif isinstance(link_to_bar, DiscreteBar):
            self.link_to_values[link_to_bar.name] = [
                ((self.norm_value(con_val), link_to_bar.values[dis_val]), str(self.norm_value(con_val)))
                for con_val, dis_val in
                zip(value_dictionary[self.name],
                    value_dictionary[link_to_bar.name])]
        elif isinstance(link_to_bar, ContinuousBar):
            self.link_to_values[link_to_bar.name] = [
                ((self.norm_value(con_val1), link_to_bar.norm_value(con_val2)), str(self.norm_value(con_val1))) for
                con_val1, con_val2 in
                zip(value_dictionary[self.name], value_dictionary[link_to_bar.name])]

    def norm_value(self, val):
        return (val - self.min_value) / (self.max_value - self.min_value)

    def set_plot_info(self, coord_tup):
        self.x_loc, (self.y_loc, self.y_min, self.y_max) = coord_tup

    def val_to_y_loc(self, val):
        return self.y_min + (self.y_max - self.y_min) * val

    def draw(self, surface):
        surface.axvline(self.x_loc, self.y_min, self.y_max, c='black')
        self.draw_labels(surface)
        for linked_bar in self.link_to_values:
            for y_val_pair in self.link_to_values[linked_bar]:
                (this_y, link_y), color = y_val_pair
                print list(color)
                this_y = self.val_to_y_loc(this_y)
                link_y = self.link_to_bars[linked_bar].val_to_y_loc(link_y)
                surface.plot((self.x_loc, self.link_to_bars[linked_bar].x_loc), (this_y, link_y), c=color)

    def draw_labels(self, surface):
        surface.text(self.x_loc * (.975 + 1) / 2, self.y_max + 0.035, self.name, fontsize=10)
        surface.text(self.x_loc, self.y_min, self.min_value, fontsize=10)
        surface.text(self.x_loc, self.y_max, self.max_value, fontsize=10)


if __name__ == "__main__":
    plot_dictionary = {
        'Issue Type': ['Material', 'Process'],
        'Disposition': ['Rework', 'Reject', 'Conceded'],
        'Issue Code': ['Quality Control', 'Production Planning', 'Rental', 'Shipping'],
        'Cost': [0.0, 25000.00]
    }
    n = 50
    link_dictionary = {
        'Issue Type': [random.choice(plot_dictionary['Issue Type']) for _ in range(n)],
        'Disposition': [random.choice(plot_dictionary['Disposition']) for _ in range(n)],
        'Issue Code': [random.choice(plot_dictionary['Issue Code']) for _ in range(n)],
        'Cost': [random.uniform(plot_dictionary['Cost'][0], plot_dictionary['Cost'][1]) for _ in range(n)]
    }

    pp = ParallelPlot(plot_dictionary)
    for col_n, row_n in zip(range(0, 4), [1, 2, 1, 1]):
        pp.add_col(row_n)

    pp.add_bar(0, 0, bar_type='discrete', bar_values='Issue Type')
    pp.add_bar(1, 0, bar_type='dummy')
    pp.add_bar(1, 1, bar_type='discrete', bar_values='Disposition')
    pp.add_bar(2, 0, bar_type='discrete', bar_values='Issue Code')
    pp.add_bar(3, 0, bar_type='continuous', bar_values='Cost')

    pp.link(link_dictionary)

    pp.draw('pp.jpg')
