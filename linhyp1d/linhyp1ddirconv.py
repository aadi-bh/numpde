# This uses a cell centered grid, unlike other codes.
# 
# python linhyp1ddirconv.py -ic smooth -scheme LW -N 20 40 80 160 320 640 -rbc 1
# python linhyp1ddirconv.py -ic smooth -scheme LW -N 20 40 80 160 320 640 -rbc 2
# 
import numpy as np
import matplotlib.pyplot as plt
import argparse
from prettytable import PrettyTable
from ic import *

def update_ftbs(nu, u):
    unew = np.empty_like(u)
    unew[1:] = (1-nu)*u[1:] + nu*u[0:-1]
    unew[0] = unew[-1]
    return unew

def update_lw(nu, u):
    unew = np.empty_like(u)
    unew[1:-1] = u[1:-1] - 0.5*nu*(u[2:]-u[0:-2]) \
                + 0.5*nu**2*(u[0:-2] - 2*u[1:-1] + u[2:])
    return unew

# N = number of cells in [xmin,xmax]
def solve(N, cfl, scheme, rbc, Tf, uinit):
    xmin, xmax = 0.0, 1.0
    a          = 1.0

    # BC on left side, use exact solution for this.
    f  = lambda t: uinit(xmin-a*t)

    h = (xmax - xmin)/N
    dt= cfl * h / np.abs(a)
    nu= a * dt / h

    # Includes one ghost cell on each side
    x = np.linspace(xmin-0.5*h, xmax+0.5*h, N+2)
    u = uinit(x)

    t, it = 0.0, 0
    while t < Tf:
        # Left ghost cell
        u[0]  = f(t+h/(2*a))
        # Right ghost cell
        if rbc == 1: # First order extrapolation
            u[-1] = u[-2]
        else:        # Second order extrapolation
            u[-1] = 2*u[-2] - u[-3]
        if scheme=='FTBS':
            u = update_ftbs(nu, u)
        elif scheme=='LW':
            u = update_lw(nu, u)
        else:
            print("Unknown scheme: ", scheme)
            return
        t += dt; it += 1

    # Extract only real cells
    u   = u[1:-1]
    x   = x[1:-1]
    err = np.abs(u - uinit(x-a*t))
    em  = np.max(err[0:-2])
    e1  = h*err[0] + h*np.sum(err[1:-2])
    err = err**2
    e2  = np.sqrt(h*err[0] + h*np.sum(err[1:-2]))
    return em,e1,e2

# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument('-N', metavar='N', type=int, nargs='+', help='Number of cells', required=True)
parser.add_argument('-cfl', type=float, help='CFL number', default=0.9)
parser.add_argument('-scheme', choices=('FTBS','LW'), help='Scheme', default='FTBS')
parser.add_argument('-Tf', type=float, help='Final time', default=1.0)
parser.add_argument('-rbc', type=int, choices=(1,2), help='Extrap order at right boundary', default=1)
parser.add_argument('-ic', choices=('smooth','hat'), help='Init cond', default='smooth')
args = parser.parse_args()

# Run the solver for different number of grid points
emax,e1,e2 = np.empty(len(args.N)),np.empty(len(args.N)),np.empty(len(args.N))
i    = 0
for N in args.N:
    print("Running for cells = ", N)
    if args.ic == "smooth":
        emax[i],e1[i],e2[i] = solve(N, args.cfl, args.scheme, args.rbc, args.Tf, smooth)
    else:
        emax[i],e1[i],e2[i] = solve(N, args.cfl, args.scheme, args.rbc, args.Tf, hat)
    i += 1

# Compute convergence rate
table = PrettyTable(['N','L1','1rate','L2','2rate','max','mrate'])
for i in range(1,len(emax)):
    pmax = np.log(emax[i-1]/emax[i])/np.log(2.0)
    p1 = np.log(e1[i-1]/e1[i])/np.log(2.0)
    p2 = np.log(e2[i-1]/e2[i])/np.log(2.0)
    table.add_row(['%4d' % args.N[i], '%e' % e1[i], '%4.2f' % p1,  
                   '%e' % e2[i],  '%4.2f' % p2,  '%e' % emax[i],  '%4.2f' % pmax])

print(table)
# Plot error convergence
plt.loglog(args.N, e1  , '*-', ms=8)
plt.loglog(args.N, e2  , 's-', ms=8)
plt.loglog(args.N, emax, 'o-', ms=8)
plt.xlabel('N')
plt.ylabel('Error norm')
plt.grid(True)
plt.title('Scheme='+args.scheme+', CFL='+str(args.cfl))
plt.legend(('$L_1$ norm','$L_2$ norm','$L_\infty$ norm'))
plt.show()
