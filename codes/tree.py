#from setup import *
from setup import OPS, OP1, OP2, VARS, DENOM, ROOT, simple_mode
import copy
import numpy as np


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
        self.p_var = p_var
        self.node_list = [[] for i in range(max_depth)]
        self.inorder = None

        self.add_root_node()
    
        for depth in range(1,self.max_depth):
            for parent_idx in range(len(self.node_list[depth - 1])):
                
                parent = self.node_list[depth - 1][parent_idx] 
                self.add_nodes(depth, parent)

        model_tree = copy.deepcopy(self.node_list)
        self.inorder = tree2str_merge(model_tree)

    def add_root_node(self):
        root = ROOT[np.random.randint(0, len(ROOT))] 
        node = Node(depth = 0, idx = 0, parent_idx = None, name = root[0], 
                    child_num = int(root[1]), var = root[2], full = root)
        self.node_list[0].append(node)
    
    def add_nodes(self, depth, parent):
        if parent.child_num == 0: 
            return
        for j in range(parent.child_num):
            # rule 1: right child of a derivative operator must be an independent variable
            if parent.name in ['d', 'd^2'] and j == 1: 
                node = DENOM[np.random.randint(0, len(DENOM))] 
                node = Node(depth = depth, idx = len(self.node_list[depth]), parent_idx = parent.idx, name = node[0],
                            child_num = int(node[1]), var = node[2], full = node)
                self.node_list[depth].append(node)
            # rule 2: leaf nodes must be variables/operands (rather than operators)
            elif depth == self.max_depth - 1:
                node = VARS[np.random.randint(0, len(VARS))]
                node = Node(depth = depth, idx = len(self.node_list[depth]), parent_idx = parent.idx, name = node[0],
                            child_num = int(node[1]), var = node[2], full = node)
                self.node_list[depth].append(node)
            else:
            # rule 3: if rules 1 and 2 do not apply, make the next node a variable/operand with probability p_var
            # (and an operator with probability 1-p_var)
                if np.random.random() <= self.p_var:
                    node = VARS[np.random.randint(0, len(VARS))]
                    node = Node(depth = depth, idx = len(self.node_list[depth]), parent_idx = parent.idx, name = node[0],
                                child_num = int(node[1]), var = node[2], full = node)
                    self.node_list[depth].append(node)
                else:
                    node = OPS[np.random.randint(0, len(OPS))]
                    node = Node(depth = depth, idx = len(self.node_list[depth]), parent_idx = parent.idx, name = node[0],
                                child_num = int(node[1]), var = node[2], full = node)
                    self.node_list[depth].append(node)
    
    def get_child_idx(self, node):
        child_idx = 0
        for i in range(node.idx):
            child_idx = child_idx + self.node_list[node.depth][i].child_num
        return child_idx
    
    def get_right_child_idx(self, node):
        return self.get_child_idx(node) + 1
            
    def mutate(self, p_mute): 
        global see_tree
        see_tree = copy.deepcopy(self.node_list)
        for depth in range(1,self.max_depth):
            for parent_idx in range(len(self.node_list[depth - 1])):
                parent = self.node_list[depth - 1][parent_idx]
                if parent.child_num == 0:
                    continue
                for j in range(parent.child_num):  
                    mute = np.random.choice([True, False], p=([p_mute, 1-p_mute]))
                    # rule 1: 
                    if mute == False:
                        continue
                    current = self.node_list[depth][self.get_child_idx(parent) + j]
                    temp = current.name
                    num_child = current.child_num  
                    # print('mutate!')
                    if num_child == 0: 
                        node = VARS[np.random.randint(0, len(VARS))] # rule 2: 
                        while node[0] == temp or (parent.name in ['d', 'd^2'] and node[0] not in DENOM[:, 0]): # rule 3: 
                            if simple_mode and parent.name in ['d', 'd^2'] and node[0] == 'x': # simple_mode中
                                break                            
                            node = VARS[np.random.randint(0, len(VARS))] 
                        new_node = Node(depth=depth, idx=self.get_child_idx(parent) + j, parent_idx=parent_idx, name=node[0],
                                    child_num=int(node[1]), var=node[2], full=node)
                        self.node_list[depth][self.get_child_idx(parent) + j] = new_node 
                    else: 
                        if num_child == 1:
                            node = OP1[np.random.randint(0, len(OP1))]
                            while node[0] == temp:  
                                node = OP1[np.random.randint(0, len(OP1))]
                        elif num_child == 2:
                            node = OP2[np.random.randint(0, len(OP2))]
                            right = self.node_list[depth + 1][self.get_right_child_idx(current)].name
                            while node[0] == temp or (node[0] in ['d', 'd^2'] and right not in DENOM[:, 0]): # rule 4
                                node = OP2[np.random.randint(0, len(OP2))]
                        else:
                            raise NotImplementedError("Error occurs!")

                        new_node = Node(depth=depth, idx=self.get_child_idx(parent) + j, parent_idx=parent_idx, name=node[0],
                                    child_num=int(node[1]), var=node[2], full=node)
                        self.node_list[depth][self.get_child_idx(parent) + j] = new_node

        model_tree = copy.deepcopy(self.node_list)
        self.inorder = tree2str_merge(model_tree)


if __name__ == '__main__':
    tree = Tree(max_depth = 4, p_var = 0.5)
    print(tree.inorder)
    tree.mutate(p_mute = 1)
    print(tree.inorder)

