from tree import *
from PDE_find import Train
from configure import aic_ratio
from setup import default_names, num_default, u
import warnings
warnings.filterwarnings('ignore')


class PDE:
    
    def __init__(self, depth, max_num_trees, p_var):
        self.depth = depth
        self.p_var = p_var
        self.num_trees = np.random.randint(max_num_trees+1)
        self.tree_list = []
        for i in range(self.num_trees):
            self.tree_list.append(Tree(depth, p_var))

    def mutate(self, p_mute):
        for i in range(self.num_trees):  
            self.tree_list[i].mutate(p_mute)

    def replace(self):
        if len(self.tree_list) == 0:
            NotImplementedError('replace error')
            
        new_tree = Tree(self.depth, self.p_var)
        idx = np.random.randint(self.num_trees)  
        self.tree_list[idx] = new_tree

    def visualize(self): 
        name = ''
        for i in range(self.num_trees):
            if i != 0:
                name += '+'
            name += self.tree_list[i].inorder
        return name

    def concise_visualize(self): 
        name = ''
        tree_list = copy.deepcopy(self.tree_list)
        tree_list, coefficients = evaluate_mse(tree_list, True)
        coefficients = coefficients[:, 0]
        # print(len(tree_list), len(coefficients))
        for i in range(len(coefficients)):
            if np.abs(coefficients[i]) < 1e-4: 
                continue
            if i != 0 and name != '':
                name += ' + '
            name += str(round(np.real(coefficients[i]), 4))
            if i < num_default: 
                name += default_names[i]
            else:
                name += tree_list[i-num_default].inorder 
        return name


def evaluate_mse(pde, is_list=False):
    if is_list:
        terms = pde
    else:
        terms = pde.tree_list
    terms_values = np.zeros((u.shape[0] * u.shape[1], len(terms)))
    delete_ix = []
    for ix, term in enumerate(terms):
        tree_list = term.tree
        max_depth = len(tree_list)

        # 先搜索倒数第二层，逐层向上对数据进行运算直到顶部；排除底部空层
        for i in range(2, max_depth+1):
            # 如果下面一层是空的，说明这一层肯定不是非空的倒数第二层
            if len(tree_list[-i+1]) == 0:
                continue
            else: # 这一层是非空至少倒数第二层，一个一个结点看过去
                for j in range(len(tree_list[-i])):
                    # 如果这一结点没有孩子，继续看右边的结点有没有
                    if tree_list[-i][j].child_num == 0:
                        continue

                    # 这一结点有一个孩子，用自己的运算符对孩子的cache进行操作
                    elif tree_list[-i][j].child_num == 1:
                        child_node = tree_list[-i+1][tree_list[-i][j].child_st]
                        tree_list[-i][j].cache = tree_list[-i][j].cache(child_node.cache)
                        child_node.cache = child_node.var  # 重置

                    # 这一结点有一两个孩子，用自己的运算符对两孩子的cache进行操作
                    elif tree_list[-i][j].child_num == 2:
                        child1 = tree_list[-i+1][tree_list[-i][j].child_st]
                        child2 = tree_list[-i+1][tree_list[-i][j].child_st+1]

                        if tree_list[-i][j].name in {'d', 'd^2'}:
                            what_is_denominator = child2.name
                            if what_is_denominator == 't':
                                tmp = dt
                            elif what_is_denominator == 'x':
                                tmp = dx
                            else:
                                raise NotImplementedError()

                            if not isfunction(tree_list[-i][j].cache):
                                pdb.set_trace()
                                tree_list[-i][j].cache = tree_list[-i][j].var

                            tree_list[-i][j].cache = tree_list[-i][j].cache(child1.cache, tmp, what_is_denominator)

                        else:
                            if isfunction(child1.cache) or isfunction(child2.cache):
                                pdb.set_trace()
                            tree_list[-i][j].cache = tree_list[-i][j].cache(child1.cache, child2.cache)
                        child1.cache, child2.cache = child1.var, child2.var  # 重置

                    else:
                        NotImplementedError()

        if not any(tree_list[0][0].cache.reshape(-1)):  # 如果全是0，无法收敛且无意义
            delete_ix.append(ix)
            tree_list[0][0].cache = tree_list[0][0].var  # 重置缓冲池
            # print('0')
            # pdb.set_trace()
        else:
            terms_values[:, ix:ix+1] = tree_list[0][0].cache.reshape(-1, 1)  # 把归并起来的该term记录下来
            tree_list[0][0].cache = tree_list[0][0].var  # 重置缓冲池
            # print('not 0')
            # pdb.set_trace()

    move = 0
    for ixx in delete_ix:
        if is_term:
            terms.pop(ixx - move)
        else:
            pde.tree_list.pop(ixx-move)
            pde.num_trees -= 1 
        terms_values = np.delete(terms_values, ixx-move, axis=1)
        move += 1  

    if False in np.isfinite(terms_values) or terms_values.shape[1] == 0:
        # pdb.set_trace()
        error = np.inf
        aic = np.inf
        w = 0

    else:
        # 2D --> 1D
        terms_values = np.hstack((default_terms, terms_values))
        w, loss, mse, aic = Train(terms_values, ut.reshape(n * m, 1), 0, 1, aic_ratio)

    if is_term:
        return terms, w
    else:
        return aic, w


if __name__ == '__main__':
    pde = PDE(depth=4, max_width=3, p_var=0.5)
    evaluate_mse(pde)
    pde.mutate(p_mute=0.1)
    pde.replace()

