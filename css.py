import sys
import zlib
import random
import tinycss
import argparse

class Node(set):
  def __init__(self, data):
    self.data = data
  def __hash__(self):
    return hash(self.data)
  def __str__(self):
    return self.data

class Left(Node):pass
class Right(Node):pass

class BiGraph(object):
  def __init__(self):
    self.nodes = {}
    self.left  = set()
    self.right = set()

  @property
  def edges(self):
    for l in self.left:
      for r in self.right:
        if r in l:
          yield l, r

  @property
  def contents(self):
    return self.left | self.right

  def add(self, node):
    if type(node) is Left:
      self.left.add(node)
    else:
      self.right.add(node)

  def connect(self, ldata, rdata):
    l = self.nodes.setdefault(ldata, Left(ldata))
    r = self.nodes.setdefault(rdata, Right(rdata))
    self.add(l)
    self.add(r)
    l.add(r)
    r.add(l)

class BiClique(BiGraph):
  def __init__(self, covering, contents):
    super(BiClique, self).__init__()

    self.covering = covering
    self.graph = covering.graph
    self.nodes = self.graph.nodes

    for node in contents:
      self.add(node)

  def __str__(self):
    return "%s{%s}" % (",".join(map(str, self.left)), ";".join(map(str, self.right)))

  def can_merge(self, other):
    sln = self.graph.left.intersection(*self.right)
    srn = self.graph.right.intersection(*self.left)
    oln = self.graph.left.intersection(*other.right)
    orn = self.graph.right.intersection(*other.left)
    return (self.left  <= oln and self.right  <= orn and
            other.left <= sln and other.right <= srn)

class Covering(set):
  def __init__(self, graph, bicliques=[]):
    self.graph = graph

    for biclique in bicliques:
      self.add(biclique)

  @property
  def cost(self):
    if self.graph.gzip in xrange(1, 10):
      return len(zlib.compress(str(self), self.graph.gzip))
    return len(str(self))

  def __hash__(self):
    return hash(frozenset(self))

  def __str__(self):
    return "".join(map(str, self))

  def cover(self, edges):
    """Find subset of bicliques covering the given set of edges

    We do this in a simple yet dumb manner by selecting random bicliques which
    cover the set of edges until it is completely covered. Although there are
    probably better heuristics, this works sufficiently well in practice.
    """
    copy, remaining = set(self), edges
    while edges:
      biclique = random.sample(copy, 1)[0]
      if set(biclique.edges) & remaining:
        remaining -= set(biclique.edges)
        copy.remove(biclique)
        yield biclique

  def crossover(self, other):
    """Crossover with another covering to generate a new pair of coverings

    We first extract a random half of bicliques from the first covering and then
    find an random subset of bicliques of the second covering which contains all
    edges not present in the first subset, this gives a first offspring. We then
    repeat the same process the other way round to compute the second offspring.
    """
    sb1 = set(random.sample(self, len(self)/2))
    ob2 = set(other.cover(set(self.graph.edges) - set().union(*(set(b.edges) for b in sb1))))

    ob1 = other - ob2
    sb2 = set(self.cover(set(other.graph.edges) - set().union(*(set(b.edges) for b in ob1))))

    sb1ob2 = Covering(self.graph, (BiClique(self, b.contents) for b in (sb1 | ob2)))
    sb2ob1 = Covering(self.graph, (BiClique(self, b.contents) for b in (sb2 | ob1)))
    return sb1ob2, sb2ob1

  def mutate_merge(self):
    """Merge (if possible) two bicliques together to form one biclique
    """
    try:
      b1 = random.sample(self, 1)[0]
      b2 = random.sample(set(b2 for b2 in self if b1.can_merge(b2) and b1 != b2), 1)[0]
      self.remove(b1)
      self.remove(b2)
      self.add(BiClique(self, b1.contents | b2.contents))
    except ValueError:
      pass

  def mutate_split(self):
    """Split (if possible) one biclique into two disting bicliques
    """
    splittable = [b for b in self if len(b.right) > 1 or len(b.left) > 1]
    if splittable:
      b = random.sample(splittable, 1)[0]
      s1, s2 = (b.left, b.right) if random.random() < 0.5 else (b.right, b.left)
      if len(s1) == 1:
        s1, s2 = s2, s1

      nbl1 = set(random.sample(s1, random.randint(1, len(s1) - 1)))
      nbl2 = s1 - nbl1
      self.add(BiClique(self, nbl1 | s2))
      self.add(BiClique(self, nbl2 | s2))
      self.remove(b)

  def mutate(self):
    """Mutate a covering by either merging two bicliques into one or splitting
    one into two.

    In practice, it seems it is more interesting to merge more frequently than
    to split, hence the higher probability.
    """
    if random.random() < 0.8:
      self.mutate_merge()
    else:
      self.mutate_split()

  def copy(self):
    covering = Covering(self.graph)
    for b in self:
      covering.add(BiClique(covering, b.contents))
    return covering

class CSS(BiGraph):
  def __init__(self, bicliques, gzip=0):
    super(CSS, self).__init__()
    self.gzip = gzip

    self.population_size = 30
    self.elite = 4
    self.max_steps = 200
    self.constant_stop = 35
    self.crossover_ratio = 0.8
    self.mutation_ratio = 0.1

    self.base_covering = Covering(self)
    for bl, br in bicliques:
      for l in bl:
        for r in br:
          self.connect(l, r)
      self.base_covering.add(BiClique(self.base_covering, (self.nodes[node] for node in (bl | br))))

  def select(self, population, w, s):
    """Select a covering in the given population

    Since we aim for a low cost, we select a random covering with a probability
    proportional to `max(costs) - cost`.
    """
    n = len(population)
    idx = 0
    target = random.randint(0, n * (w + 1) - s)
    while True:
      target -= ((w + 1) - population[idx].cost)
      if target <= 0:
        return population[idx]
      idx += 1

  def crossover(self, prob, c1, c2):
    if random.random() < prob:
      return c1.crossover(c2)
    else:
      return c1.copy(), c2.copy()

  def mutate(self, prob, c):
    for i in range(len(c)):
      if random.random() < prob:
        c.mutate()
    return c

  def compress(self):
    print >> sys.stderr, "Cost at beginning:", self.base_covering.cost
    previous, rounds = None, 0

    population = sorted(
        [self.base_covering.copy() for i in xrange(self.population_size)],
        key=lambda x: x.cost)

    for i in range(self.max_steps):
      print >> sys.stderr, "Generation", i

      nextgen = population[:self.elite] # copy the best covering in the previous generation
      w, s = population[-1].cost, sum(c.cost for c in population)

      while len(nextgen) < self.population_size:
        c1 = self.select(population, w, s)
        c2 = self.select(population, w, s)
        c1, c2 = self.crossover(self.crossover_ratio, c1, c2)
        self.mutate(self.mutation_ratio, c1)
        self.mutate(self.mutation_ratio, c2)
        nextgen.append(c1)
        nextgen.append(c2)
      population = sorted(list(nextgen), key=lambda covering: covering.cost)

      best = population[0]
      print >> sys.stderr, " best compression: ", best.cost
      if previous == best.cost:
        count += 1
        if count > self.constant_stop:
          break
      else:
        previous = best.cost
        count = 1
    return best

# CSS Parser boilerplate
class CSSStarHackParser(tinycss.CSSPage3Parser):
  def parse_declaration(self, tokens):
    has_star_hack = (tokens[0].type == 'DELIM' and tokens[0].value == '*')
    if has_star_hack:
      tokens = tokens[1:]
    declaration = super(CSSStarHackParser, self).parse_declaration(tokens)
    declaration.has_star_hack = has_star_hack
    return declaration

def parse(src):
  parser = tinycss.make_parser(CSSStarHackParser)
  stylesheet = parser.parse_stylesheet_bytes(src)

  # Parser fails on a few CSS3 constructs, warn the user and ignore errors
  for err in stylesheet.errors:
    print >> sys.stderr, "!!", err

  for rule in stylesheet.rules:
    if rule.at_keyword is None:
      bl, br = set(), set()
      for left in rule.selector.as_css().split(','):
        for declaration in rule.declarations:
          l = left.strip()
          r = ("%s:%s" % (declaration.name, declaration.value.as_css())).strip()
          if declaration.priority: r += "!important"
          if declaration.has_star_hack: r = "*" + r
          bl.add(l)
          br.add(r)
      yield bl, br

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('-g', '--gzip', dest='gzip', type=int, default=0,
                    help='Level of gzip compression. Default no compression')
  parser.add_argument('-o', '--output', dest='out', type=str, default='',
                      help='output file name. If none, use STDOUT')
  parser.add_argument('fname', type=str, nargs='+', help='input file name')

  args = parser.parse_args()

  source = ""
  for fname in args.fname:
    with open(fname) as f:
      source += f.read()

  css = CSS(parse(source), args.gzip)
  res = css.compress()
  if args.out:
    with open(args.out, 'w') as f:
      f.write(str(res))
  else: print str(res)
  print >> sys.stderr, "Compressed file: %s characters (%d%% of original)" % (
      res.cost, 100 * res.cost / css.base_covering.cost)
