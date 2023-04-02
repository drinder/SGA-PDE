from setup import *
import copy
import numpy as np

class Node:
    
    """
        depth: depth of the node
        idx: index of the node within its layer
        parent_idx: index of the node's parent within the parent's layer
        name: string representing the node's name (full[0])
        child_num: number of children (full[1])
        var: full[2]
        cache: 
        status: 
        full: e.g. ['sin', 1, np.sin], ['*', 2, np.multiply] 
    """
    
    def __init__(self, depth, idx, parent_idx, name, child_num, var, full):
        
        self.depth = depth
        self.idx = idx
        self.parent_idx = parent_idx
        self.name = name
        self.child_num = child_num
        self.var = var
        self.cache = copy.deepcopy(var)
        self.status = self.child_num
        self.full = full

    def __str__(self): 
        return self.name

    def reset_status(self):
        self.status = self.child_num


class Tree: 
    
    """
        max_depth: maximum depth of the tree
        p_var: probability of a node being a variable/operand
               (as opposed to an operator)
    """
        
    def __init__(self, max_depth, p_var):
        
        self.max_depth = max_depth
        self.tree = [[] for i in range(max_depth)]
        self.preorder = None
        self.inorder = None

        self.add_root_node()
    
        for depth in range(1,max_depth):
            for parent_idx in range(len(self.tree[depth - 1])): 
                parent = self.tree[depth - 1][parent_idx] 
                if parent.child_num == 0: 
                    continue
                for j in range(parent.child_num):
                    # rule 1: right child of a derivative operator must be an independent variable
                    if parent.name in ['d', 'd^2'] and j == 1: 
                        node = DENOM[np.random.randint(0, len(DENOM))] 
                        node = Node(depth = depth, idx = len(self.tree[depth]), parent_idx = parent_idx, name = node[0],
                                    child_num = int(node[1]), var = node[2], full = node)
                        self.tree[depth].append(node)
                    # rule 2: leaf nodes must be variables/operands (rather than operators)
                    elif depth == max_depth - 1:
                        node = VARS[np.random.randint(0, len(VARS))]
                        node = Node(depth = depth, idx = len(self.tree[depth]), parent_idx = parent_idx, name = node[0],
                                    child_num = int(node[1]), var = node[2], full = node)
                        self.tree[depth].append(node)
                    else:
                    # rule 3: if rules 1 and 2 do not apply, make the next node a variable/operand with probability p_var
                    # (and an operator with probability 1-p_var)
                        if np.random.random() <= p_var:
                            node = VARS[np.random.randint(0, len(VARS))]
                            node = Node(depth = depth, idx = len(self.tree[depth]), parent_idx = parent_idx, name = node[0],
                                        child_num = int(node[1]), var = node[2], full = node)
                            self.tree[depth].append(node)
                        else:
                            node = OPS[np.random.randint(0, len(OPS))]
                            node = Node(depth = depth, idx = len(self.tree[depth]), parent_idx = parent_idx, name = node[0],
                                        child_num = int(node[1]), var = node[2], full = node)
                            self.tree[depth].append(node)

        ret = []
        #dfs(ret, self.tree, depth = 0, idx = 0)
        self.preorder = ' '.join([x for x in ret])
        model_tree = copy.deepcopy(self.tree)
        self.inorder = tree2str_merge(model_tree)

    def add_root_node(self):
        root = ROOT[np.random.randint(0, len(ROOT))] # e.g. ['sin', 1, np.sin], ['*', 2, np.multiply] 
        node = Node(depth = 0, idx = 0, parent_idx = None, name = root[0], 
                    child_num = int(root[1]), var = root[2], full = root)
        self.tree[0].append(node)
    
    def get_child_idx(self, node):
        child_idx = 0
        for i in range(node.idx):
            child_idx = child_idx + self.tree[node.depth][i].child_num
        return child_idx
    
    def get_right_child_idx(self, node):
        return self.get_child_idx(node) + 1
            
    def mutate(self, p_mute): 
        global see_tree
        see_tree = copy.deepcopy(self.tree)
        depth = 1
        while depth < self.max_depth:
            idx_this_depth = 0  
            for parent_idx in range(len(self.tree[depth - 1])):
                parent = self.tree[depth - 1][parent_idx]
                if parent.child_num == 0:
                    continue
                for j in range(parent.child_num):  
                    not_mute = np.random.choice([True, False], p=([1 - p_mute, p_mute]))
                    # rule 1: 
                    if not_mute:
                        continue
                    current = self.tree[depth][idx_this_depth]
                    temp = current.name
                    num_child = current.child_num  
                    # print('mutate!')
                    if num_child == 0: 
                        node = VARS[np.random.randint(0, len(VARS))] # rule 2: 
                        while node[0] == temp or (parent.name in ['d', 'd^2'] and node[0] not in DENOM[:, 0]): # rule 3: 
                            if simple_mode and parent.name in ['d', 'd^2'] and node[0] == 'x': # simple_mode中
                                break                            
                            node = VARS[np.random.randint(0, len(VARS))] 
                        new_node = Node(depth=depth, idx=idx_this_depth, parent_idx=parent_idx, name=node[0],
                                    child_num=int(node[1]), var=node[2], full=node)
                        self.tree[depth][idx_this_depth] = new_node 
                    else: 
                        if num_child == 1:
                            node = OP1[np.random.randint(0, len(OP1))]
                            while node[0] == temp:  
                                node = OP1[np.random.randint(0, len(OP1))]
                        elif num_child == 2:
                            node = OP2[np.random.randint(0, len(OP2))]
                            right = self.tree[depth + 1][self.get_right_child_idx(current)].name
                            while node[0] == temp or (node[0] in ['d', 'd^2'] and right not in DENOM[:, 0]): # rule 4
                                node = OP2[np.random.randint(0, len(OP2))]
                        else:
                            raise NotImplementedError("Error occurs!")

                        new_node = Node(depth=depth, idx=idx_this_depth, parent_idx=parent_idx, name=node[0],
                                    child_num=int(node[1]), var=node[2], full=node)
                        self.tree[depth][idx_this_depth] = new_node
                    idx_this_depth += 1
            depth += 1

        ret = []
        #dfs(ret, self.tree, depth=0, idx=0)
        self.preorder = ' '.join([x for x in ret])
        model_tree = copy.deepcopy(self.tree)
        self.inorder = tree2str_merge(model_tree)


# def dfs(ret, a_tree, depth, idx): 
#     # print(depth, idx) 
#     node = a_tree[depth][idx]
#     ret.append(node.name) 
#     for ix in range(node.child_num):
#         if node.child_st is None:
#             continue
#         dfs(ret, a_tree, depth+1, node.child_st + ix) #进入下一层中下一个节点对应的子节点


def tree2str_merge(a_tree):
    for i in range(len(a_tree) - 1, 0, -1):
        for node in a_tree[i]:
            if node.status == 0:
                if a_tree[node.depth-1][node.parent_idx].status == 1:
                    if a_tree[node.depth-1][node.parent_idx].child_num == 2:
                        a_tree[node.depth-1][node.parent_idx].name = a_tree[node.depth-1][node.parent_idx].name + ' ' + node.name + ')'
                    else:
                        a_tree[node.depth-1][node.parent_idx].name = '( ' + a_tree[node.depth-1][node.parent_idx].name + ' ' + node.name + ')'
                elif a_tree[node.depth-1][node.parent_idx].status > 1:
                    a_tree[node.depth-1][node.parent_idx].name = '(' + node.name + ' ' + a_tree[node.depth-1][node.parent_idx].name
                a_tree[node.depth-1][node.parent_idx].status -= 1
    return a_tree[0][0].name


# class Point:
#     def __init__(self, idx, name, child_num, child_idx=[]):
#         """
#             1. idx: 当前序列的第几个节点
#             2. parent_idx: 父节点是第几个节点
#             3. name: 节点名称
#             4. child_num: 节点拥有几个孩子节点
#             5. child_idx: 孩子节点是序列的第几个
#         """
#         self.idx = idx
#         self.name = name
#         self.child_num = child_num
#         self.child_idx = child_idx

#     def __str__(self):
#         return self.name

#     def add_child(self, ix):
#         self.child_idx.append(ix)


# def is_an_equation(seq):  # e.g. (+ u - u u)
#     def split(seq, idx):
#         # last element is an op
#         if idx >= len(seq): return np.inf

#         # idx is the current node
#         op = ALL[:, 0]
#         root = ALL[np.where(op == seq[idx])][0]
#         node = Point(idx=idx, name=root[0], child_num=int(root[1]))

#         if node.child_num != 0:
#             node.child_idx.append(idx + 1)  # might be wrong for the last node, not fatal though
#             new_idx = split(seq, idx + 1)  # first child
#             if node.child_num != 1:  # other children
#                 node.child_idx.append(new_idx)
#                 new_idx = split(seq, new_idx)
#             return new_idx

#         return idx + 1

#     idx = 0
#     end_idx = split(seq, idx)
#     if end_idx != len(seq):
#         return False
#     return True


if __name__ == '__main__':
    tree = Tree(max_depth = 4, p_var = 0.5)
    print(tree.inorder)
    tree.mutate(p_mute = 1)
    print(tree.inorder)

